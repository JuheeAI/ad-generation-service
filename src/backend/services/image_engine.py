import os
import io
import base64
import logging
import json
import torch
import requests
import numpy as np
from PIL import Image
from dotenv import load_dotenv

from diffusers import Flux2Pipeline
from transformers import BitsAndBytesConfig
from huggingface_hub import get_token

load_dotenv()

MY_HF_TOKEN = os.getenv("HF_TOKEN")

os.environ["HF_HOME"] = "/workspace/huggingface"
os.environ["HF_HUB_CACHE"] = "/workspace/huggingface/hub"
os.environ["HF_TOKEN"] = MY_HF_TOKEN

def remote_text_encoder(prompt, logger):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if not prompt: return None
    
    api_url = "https://remote-text-encoder-flux-2.huggingface.co/predict"
    if logger: logger.info(f"📡 Sending prompt to Remote API: {api_url}")
    
    try:
        response = requests.post(
            api_url,
            json={"prompt": prompt},
            headers={
                "Authorization": f"Bearer {MY_HF_TOKEN}",
                "Content-Type": "application/json"
            },
            timeout=120
        )
        
        if response.status_code != 200:
            if logger: logger.error(f"API Error ({response.status_code}): {response.text}")
            return None
            
        data = torch.load(io.BytesIO(response.content))
        
        if isinstance(data, (tuple, list)):
            if logger: logger.info(f"Received Tuple/List. Using index 0.")
            return data[0].to(device)
        else:
            if logger: logger.info("Received Single Tensor.")
            return data.to(device)

    except Exception as e:
        if logger: logger.error(f"Remote Encoder Failed: {e}")
        return None

class OutputManager:
    def __init__(self, output_dir="outputs", logger=None):
        self.output_dir = output_dir
        self.logger = logger or logging.getLogger("AdImagePipeline")
        os.makedirs(self.output_dir, exist_ok=True)

    def save(self, image: Image.Image, base_filename: str) -> str:
        path = os.path.join(self.output_dir, f"{base_filename}.png")
        image.save(path)
        if self.logger: self.logger.info(f"Image saved to {path}")
        return path

    def to_base64(self, image: Image.Image) -> str:
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

class ModelManager:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.loaded_models = {}

    def load_flux_model(self):
        key = "flux_pipeline"
        if key in self.loaded_models: return self.loaded_models[key]
        
        self.logger.info("Loading FLUX.2 [dev] (4-bit)...")

        pipe = Flux2Pipeline.from_pretrained(
            "diffusers/FLUX.2-dev-bnb-4bit",
            text_encoder=None,
            torch_dtype=torch.bfloat16
        )

        pipe.to("cuda")
        self.loaded_models[key] = pipe
        return pipe

    def unload(self, *keys):
        keys_to_unload = keys or list(self.loaded_models.keys())
        for k in keys_to_unload:
            if k in self.loaded_models:
                del self.loaded_models[k]
                self.logger.info(f"Model '{k}' unloaded.")
        if torch.cuda.is_available(): torch.cuda.empty_cache()

class ImageGenerationPipeline:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.model_manager = ModelManager(config, logger)
        
        self.templates = {}
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            template_path = os.path.join(current_dir, "templates.json")
            with open(template_path, "r", encoding="utf-8") as f:
                self.templates = json.load(f)
        except Exception:
            self.templates["white_default"] = {"name": "화이트(기본)"}

    def _load_b64(self, b64_str):
        if not b64_str: return None
        try:
            return Image.open(io.BytesIO(base64.b64decode(b64_str))).convert("RGB")
        except Exception:
            return None

    def _create_simple_collage(self, images_dict, width, height):
        self.logger.info("Creating dynamic collage...")
        
        background = images_dict.get("background")
        model = images_dict.get("model")
        product = images_dict.get("product")
        
        if background:
            canvas = background.resize((width, height), Image.LANCZOS)
        else:
            canvas = Image.new("RGB", (width, height), (255, 255, 255))
            
        foreground_items = []
        if model: foreground_items.append(model)
        if product: foreground_items.append(product)
        
        count = len(foreground_items)
        if count == 0:
            return canvas

        slot_width = width // count
        
        for i, img in enumerate(foreground_items):
            target_w = slot_width
            ratio = target_w / img.width
            target_h = int(img.height * ratio)
            
            if target_h > height:
                target_h = height
                target_w = int(target_h * (img.width / img.height))

            resized_img = img.resize((target_w, target_h), Image.LANCZOS)
            
            x_offset = (i * slot_width) + (slot_width - target_w) // 2
            y_offset = (height - target_h) // 2 
            
            canvas.paste(resized_img, (x_offset, y_offset))
            
        return canvas

    def run(self, inputs):
        base_output_dir = "outputs"
        os.makedirs(base_output_dir, exist_ok=True)
        existing_ids = [int(d) for d in os.listdir(base_output_dir) if d.isdigit()]
        run_id = max(existing_ids, default=0) + 1
        run_output_dir = os.path.join(base_output_dir, str(run_id))
        
        output_manager = OutputManager(output_dir=run_output_dir, logger=self.logger)
        
        try:
            params = inputs.get("params", {})
            prompt_text = inputs.get("prompt")
            
            images_dict = {
                "background": self._load_b64(inputs.get("background_image")),
                "product": self._load_b64(inputs.get("product_image")),
                "model": self._load_b64(inputs.get("model_image"))
            }

            width, height = map(int, params.get("size", "1024x1024").split("x"))
            seed = int(params.get("seed")) if params.get("seed") is not None else torch.randint(0, 2**32-1, (1,)).item()
            
            self.logger.info(f"Run ID: {run_id}, Size: {width}x{height}, Seed: {seed}")

            pipe = self.model_manager.load_flux_model()

            prompt_embeds = remote_text_encoder(prompt_text, self.logger)
            if prompt_embeds is None:
                 raise ValueError("Remote Text Encoder failed.")

            is_any_image = any(img is not None for img in images_dict.values())
            collage_image = None
            
            if is_any_image:
                self.logger.info("Creating Collage for Img2Img...")
                collage_image = self._create_simple_collage(images_dict, width, height)
                output_manager.save(collage_image, "00_collage_input")

            self.logger.info("✨ Generating Final Image...")
            
            final_image = pipe(
                prompt_embeds=prompt_embeds,
                image=collage_image,
                strength=0.85 if collage_image else None,
                height=height if not collage_image else None,
                width=width if not collage_image else None,
                guidance_scale=4.0, 
                num_inference_steps=30,
                generator=torch.Generator("cuda").manual_seed(seed)
            ).images[0]

            if params.get("file_saved", True):
                path = output_manager.save(final_image, f"final_ad_{seed}")
                return {"status": "success", "filepath": path, "seed": seed}
            else:
                return {"status": "success", "image_base64": output_manager.to_base64(final_image), "seed": seed}

        except Exception as e:
            self.logger.error(f"Pipeline Failed: {e}")
            import traceback
            traceback.print_exc() 
            return {"status": "error", "message": str(e)}
