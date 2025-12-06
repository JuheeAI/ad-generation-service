import os
import io
import base64
import logging
import json
import torch
import requests
import numpy as np
from PIL import Image

from diffusers import FluxPipeline
from transformers import BitsAndBytesConfig
from huggingface_hub import get_token

from ..core import config
from .prompt_utils import build_ad_prompt_compose

os.environ["HF_HOME"] = "/workspace/huggingface"
os.environ["HF_HUB_CACHE"] = "/workspace/huggingface/hub"

def remote_text_encoder(prompt, device):
    try:
        response = requests.post(
            "https://remote-text-encoder-flux-2.huggingface.co/predict",
            json={"prompt": prompt},
            headers={
                "Authorization": f"Bearer {get_token()}",
                "Content-Type": "application/json"
            }
        )
        if response.status_code != 200:
            raise Exception(f"API Error: {response.text}")
        prompt_embeds = torch.load(io.BytesIO(response.content))
        return prompt_embeds.to(device)
    except Exception as e:
        print(f"Remote Encoder Failed: {e}. Fallback logic needed.")
        return None

class OutputManager:
    def __init__(self, output_dir="outputs", logger=None):
        self.output_dir, self.logger = output_dir, logger or logging.getLogger("AdImagePipeline")
        os.makedirs(self.output_dir, exist_ok=True)
    def save(self, image: Image.Image, base_filename: str) -> str:
        path = os.path.join(self.output_dir, f"{base_filename}.png")
        image.save(path)
        if self.logger: self.logger.info(f"Image saved to {path}")
        return path
    def to_base64(self, image: Image.Image) -> str:
        buf = io.BytesIO()
        image.save(buf, format="PNG"); return base64.b64encode(buf.getvalue()).decode("utf-8")

class ModelManager:
    def __init__(self, config, logger):
        self.config, self.logger, self.loaded_models = config, logger, {}

    def load_flux_model(self):
        key = "flux_pipeline"
        if key in self.loaded_models: return self.loaded_models[key]
        
        self.logger.info("Loading FLUX.2 [dev] with 4-bit Quantization...")

        pipe = FluxPipeline.from_pretrained(
            "diffusers/FLUX.2-dev-bnb-4bit", 
            torch_dtype=torch.bfloat16
        )

        pipe.enable_model_cpu_offload()
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
        self.config, self.logger = config, logger
        self.model_manager = ModelManager(config, logger)
        
        self.negative_prompt = "low quality, text, watermark, bad anatomy"
        
        self.rembg_session = None
        
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
        return Image.open(io.BytesIO(base64.b64decode(b64_str))).convert("RGB")

    def _create_simple_collage(self, images_dict, width, height):
        self.logger.info("Creating dynamic collage for multiple inputs...")
        
        valid_images = []
        if images_dict.get("background"): valid_images.append(images_dict["background"])
        if images_dict.get("model"): valid_images.append(images_dict["model"])
        if images_dict.get("product"): valid_images.append(images_dict["product"])
                
        count = len(valid_images)
        if count == 0:
            return Image.new("RGB", (width, height), (255, 255, 255))

        canvas = Image.new("RGB", (width, height), (255, 255, 255))
        
        slot_width = width // count
        
        for i, img in enumerate(valid_images):
            
            target_w = slot_width
            target_h = height
            
            img_ratio = img.width / img.height
            slot_ratio = target_w / target_h
            
            if img_ratio > slot_ratio:
                new_w = target_w
                new_h = int(target_w / img_ratio)
            else:
                new_h = target_h
                new_w = int(target_h * img_ratio)
                
            resized_img = img.resize((new_w, new_h), Image.LANCZOS)
            
            x_offset = (i * slot_width) + (slot_width - new_w) // 2
            y_offset = (height - new_h) // 2
            
            canvas.paste(resized_img, (x_offset, y_offset))
            
        return canvas

    def run(self, inputs):
        base_output_dir = "outputs"
        os.makedirs(base_output_dir, exist_ok=True)
        run_id = max(map(int, [d for d in os.listdir(base_output_dir) if d.isdigit()]), default=0) + 1
        run_output_dir = os.path.join(base_output_dir, str(run_id))
        output_manager = OutputManager(output_dir=run_output_dir, logger=self.logger)
        
        try:
            params = inputs.get("params", {})
            prompt_text = inputs.get("prompt")
            product_image_b64 = inputs.get("product_image")
            model_image_b64 = inputs.get("model_image")
            
            product_image = self._load_b64(product_image_b64)
            model_image = self._load_b64(model_image_b64)

            width, height = map(int, params.get("size", "1024x1024").split("x"))
            seed = int(params.get("seed")) if params.get("seed") is not None else torch.randint(0, 2**32-1, (1,)).item()
            
            self.logger.info(f"Run ID: {run_id}, Size: {width}x{height}, Seed: {seed}")

            pipe = self.model_manager.load_flux_model()

            is_image_provided = (product_image is not None) or (model_image is not None)
            final_image = None

            # Case A: 텍스트만 있는 경우
            if not is_image_provided:
                self.logger.info("Mode: Text-to-Image")
                final_image = pipe(
                    prompt=prompt_text,
                    height=height,
                    width=width,
                    guidance_scale=3.5, 
                    num_inference_steps=30,
                    generator=torch.Generator(self.config.DEVICE).manual_seed(seed)
                ).images[0]

            # Case B: 이미지가 있는 경우
            else:
                self.logger.info("Mode: Collage & Generate (Img2Img)")

                collage_image = self._create_simple_collage(
                    model_image, product_image, width, height
                )
                output_manager.save(collage_image, "00_collage_input")
                
                self.logger.info("Generating final image with FLUX...")

                final_image = pipe(
                    prompt=prompt_text,
                    image=collage_image, 
                    strength=0.85,      
                    guidance_scale=3.5,
                    num_inference_steps=40,
                    generator=torch.Generator(self.config.DEVICE).manual_seed(seed)
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
        
        finally:
            self.model_manager.unload()
            if torch.cuda.is_available(): 
                torch.cuda.empty_cache()
