import os
import sys

# [중요] 모델 저장 경로를 Volume Disk(/workspace)로 강제 변경
# 이 코드는 반드시 다른 라이브러리(diffusers, transformers) 임포트보다 위에 있어야 함
os.environ["HF_HOME"] = "/workspace/huggingface"
os.environ["HF_HUB_CACHE"] = "/workspace/huggingface/hub"

import io
import base64
import logging
import torch
import requests
import numpy as np
from PIL import Image
from huggingface_hub import login, get_token

# ==========================================
# 1. 라이브러리 임포트
# ==========================================
from diffusers import Flux2Pipeline

# ==========================================
# 2. 가짜 설정(Mock Config)
# ==========================================
class MockConfig:
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# 로그 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestPipeline")

def remote_text_encoder(prompt):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    try:
        token = get_token()
        if not token:
            logger.warning("HuggingFace Token not found. Login via huggingface-cli login.")
            return None
            
        response = requests.post(
            "https://remote-text-encoder-flux-2.huggingface.co/predict",
            json={"prompt": prompt},
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )
        if response.status_code != 200:
            logger.warning(f"Remote API Error: {response.text}")
            return None
            
        prompt_embeds = torch.load(io.BytesIO(response.content))
        return prompt_embeds.to(device)
    except Exception as e:
        logger.warning(f"Remote Encoder Failed: {e}")
        return None

# ==========================================
# 3. 파이프라인 클래스
# ==========================================
class OutputManager:
    def __init__(self, output_dir="outputs"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def save(self, image: Image.Image, base_filename: str) -> str:
        path = os.path.join(self.output_dir, f"{base_filename}.png")
        image.save(path)
        print(f"✅ Image saved: {path}")
        return path

class ImageGenerationPipeline:
    def __init__(self):
        self.logger = logger
        self.loaded_model = None

    def load_flux_model(self):
        if self.loaded_model: return self.loaded_model
        
        self.logger.info("🚀 Loading FLUX.2 [dev] (4-bit)...")
        self.logger.info(f"💾 Cache Dir: {os.environ.get('HF_HOME')}") # 경로 확인용 로그
        
        # [수정] quantization_config 제거 & 최신 diffusers 호환
        pipe = Flux2Pipeline.from_pretrained(
            "diffusers/FLUX.2-dev-bnb-4bit",
            text_encoder=None,
            torch_dtype=torch.bfloat16
        )
        
        pipe.enable_model_cpu_offload()
        self.loaded_model = pipe
        return pipe

    def _load_b64(self, b64_str):
        if not b64_str: return None
        return Image.open(io.BytesIO(base64.b64decode(b64_str))).convert("RGB")

    def _create_simple_collage(self, model_image, product_image, width, height):
        self.logger.info("🎨 Creating simple collage (Side-by-Side)...")
        canvas = Image.new("RGB", (width, height), (255, 255, 255))

        if model_image and product_image:
            target_w = width // 2
            ratio = target_w / model_image.width
            target_h = int(model_image.height * ratio)
            
            resized_model = model_image.resize((target_w, target_h), Image.LANCZOS)
            canvas.paste(resized_model, (0, (height - target_h) // 2))

            ratio_p = target_w / product_image.width
            target_h_p = int(product_image.height * ratio_p)
            resized_product = product_image.resize((target_w, target_h_p), Image.LANCZOS)
            canvas.paste(resized_product, (target_w, (height - target_h_p) // 2))

        elif model_image:
            model_image.thumbnail((width, height), Image.LANCZOS)
            mx = (width - model_image.width) // 2
            my = (height - model_image.height) // 2
            canvas.paste(model_image, (mx, my))

        elif product_image:
            product_image.thumbnail((width, height), Image.LANCZOS)
            px = (width - product_image.width) // 2
            py = (height - product_image.height) // 2
            canvas.paste(product_image, (px, py))
            
        return canvas

    def run(self, inputs):
        output_manager = OutputManager()
        
        try:
            params = inputs.get("params", {})
            prompt_text = inputs.get("prompt")
            
            product_image = self._load_b64(inputs.get("product_image"))
            model_image = self._load_b64(inputs.get("model_image"))
            
            width, height = map(int, params.get("size", "1024x1024").split("x"))
            seed = int(params.get("seed", 42))
            
            pipe = self.load_flux_model()

            collage_image = None
            if product_image or model_image:
                self.logger.info("🖼️ Mode: Collage & Generate (Img2Img)")
                
                collage_image = self._create_simple_collage(model_image, product_image, width, height)
                output_manager.save(collage_image, "debug_collage_input")
                
                self.logger.info("✨ Generating Final Image...")
                final_image = pipe(
                    prompt_embeds=remote_text_encoder(prompt_text),
                    pooled_prompt_embeds=None,
                    image=collage_image if collage_image else None,
                    strength=0.85 if collage_image else None, 
                    height=height if not collage_image else None,
                    width=width if not collage_image else None,
                    guidance_scale=4.0,
                    num_inference_steps=30,
                    generator=torch.Generator("cpu").manual_seed(seed)
                ).images[0]
            
                return output_manager.save(final_image, f"result_{seed}")

        except Exception as e:
            self.logger.error(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return None

if __name__ == "__main__":
    def image_to_b64(path):
        if not os.path.exists(path): return None
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    MODEL_IMG_PATH = "model.png" 
    PRODUCT_IMG_PATH = "product.png"

    test_inputs = {
        "prompt": "Model wearing the shoes from the product image, jumping in the air, energetic vibe, high resolution.",        "product_image": image_to_b64(PRODUCT_IMG_PATH),
        "model_image": image_to_b64(MODEL_IMG_PATH),
        "params": {
            "size": "1024x1024",
            "seed": 12345
        }
    }

    print("--- 🧪 실험 시작 ---")
    pipeline = ImageGenerationPipeline()
    result_path = pipeline.run(test_inputs)
    
    if result_path:
        print(f"--- 🎉 실험 성공! 결과물: {result_path} ---")
    else:
        print("--- 💥 실험 실패 ---")
