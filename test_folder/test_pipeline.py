import os
import sys

# ==========================================
# [필수] 토큰 설정
# ==========================================
MY_HF_TOKEN = "HF_TOKEN_FROM_ENV"

# 환경 변수 설정
os.environ["HF_HOME"] = "/workspace/huggingface"
os.environ["HF_HUB_CACHE"] = "/workspace/huggingface/hub"
os.environ["HF_TOKEN"] = MY_HF_TOKEN

import io
import base64
import logging
import torch
import requests
import traceback
from PIL import Image
from huggingface_hub import login

# 라이브러리 임포트
from diffusers import Flux2Pipeline 

# 로그 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestPipeline")

def remote_text_encoder(prompt):
    """
    API 응답이 하나든 둘이든 유연하게 처리하는 함수
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    if not prompt: return None
    
    api_url = "https://remote-text-encoder-flux-2.huggingface.co/predict"
    
    logger.info(f"📡 Sending prompt to Remote API: {api_url}")
    
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
            logger.error(f"❌ API Error ({response.status_code}): {response.text}")
            return None
            
        data = torch.load(io.BytesIO(response.content))
        
        # [데이터 확인 로직]
        # API가 튜플을 주면 첫 번째 것만 씁니다 (Flux2Pipeline 특성상)
        if isinstance(data, (tuple, list)):
            logger.info(f"📦 Received Tuple/List of length {len(data)}. Using index 0.")
            # 가이드에 따르면 Flux2Pipeline은 prompt_embeds 하나만 받으므로 
            # 튜플이 오더라도 첫번째 텐서만 넘겨주는 게 안전합니다.
            return data[0].to(device)
        else:
            logger.info("📦 Received Single Tensor.")
            return data.to(device)

    except Exception as e:
        logger.error(f"❌ Remote Encoder Failed: {e}")
        return None

class OutputManager:
    def __init__(self, output_dir="outputs"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def save(self, image: Image.Image, base_filename: str) -> str:
        path = os.path.join(self.output_dir, f"{base_filename}.png")
        image.save(path)
        logger.info(f"✅ Image saved: {path}")
        return path

class ImageGenerationPipeline:
    def __init__(self):
        self.logger = logger
        self.loaded_model = None

    def load_flux_model(self):
        if self.loaded_model: return self.loaded_model
        
        self.logger.info("🚀 Loading FLUX.2 [dev] (4-bit)...")
        self.logger.info(f"💾 Cache Dir: {os.environ.get('HF_HOME')}") 
        
        pipe = Flux2Pipeline.from_pretrained(
            "diffusers/FLUX.2-dev-bnb-4bit",
            text_encoder=None,
            torch_dtype=torch.bfloat16
        )
        
        pipe.to("cuda")
        self.loaded_model = pipe
        return pipe

    def _load_b64(self, b64_str):
        if not b64_str: return None
        return Image.open(io.BytesIO(base64.b64decode(b64_str))).convert("RGB")

    def _create_simple_collage(self, model_image, product_image, width, height):
        self.logger.info("🎨 Creating simple collage (Side-by-Side)...")
        canvas = Image.new("RGB", (width, height), (255, 255, 255))

        if not model_image and not product_image:
            return None

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
            
            # [핵심] API에서 받은 Embeddings (하나짜리 텐서)
            prompt_embeds = remote_text_encoder(prompt_text)
            
            if prompt_embeds is None:
                raise ValueError("Remote Text Encoder failed.")
            
            self.logger.info("✨ Generating Final Image...")
            
            # [핵심 수정] pooled_prompt_embeds 인자를 삭제했습니다!
            final_image = pipe(
                prompt_embeds=prompt_embeds,
                # pooled_prompt_embeds=None,  <-- 이 줄을 지웠습니다! (에러 원인)
                image=collage_image if collage_image else None,
                # strength=0.85, # 필요하다면 주석 해제
                height=height if not collage_image else None,
                width=width if not collage_image else None,
                guidance_scale=4.0,
                num_inference_steps=30,
                generator=torch.Generator("cpu").manual_seed(seed)
            ).images[0]
        
            return output_manager.save(final_image, f"result_{seed}")

if __name__ == "__main__":
    def image_to_b64(path):
        if not os.path.exists(path): return None
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    # 경로 자동 보정
    current_dir = os.path.dirname(os.path.abspath(__file__))
    MODEL_IMG_PATH = os.path.join(current_dir, "model.jpg") 
    PRODUCT_IMG_PATH = os.path.join(current_dir, "product.png")

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
    try:
        result_path = pipeline.run(test_inputs)
        if result_path:
            print(f"--- 🎉 실험 성공! 결과물: {result_path} ---")
        else:
            print("--- 💥 실험 실패 (결과 없음) ---")
    except Exception:
        print("--- 💥 치명적 오류 발생 ---")
        traceback.print_exc()