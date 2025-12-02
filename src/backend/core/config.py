import torch
import os

# 디바이스 설정
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
TORCH_DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32

# 모델 ID (Hugging Face)
# A6000은 VRAM이 넉넉하므로 Base, Refiner, ControlNet 모두 로드 가능
SDXL_BASE_MODEL_PATH = "stabilityai/stable-diffusion-xl-base-1.0"
REFINER_MODEL_PATH = "stabilityai/stable-diffusion-xl-refiner-1.0"
VAE_PATH = "madebyollin/sdxl-vae-fp16-fix" # NaN 방지용 VAE
CONTROLNET_CANNY_PATH = "diffusers/controlnet-canny-sdxl-1.0"

# IP-Adapter 설정
IP_ADAPTER_BASE_PATH = "h94/IP-Adapter"
IP_ADAPTER_WEIGHTS_PATH = "sdxl_models/ip-adapter_sdxl.bin" # diffusers가 알아서 찾음
IP_ADAPTER_IMAGE_ENCODER_PATH = "h94/IP-Adapter/models/image_encoder"

# 기타 설정
REFINER_STRENGTH = 0.3
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "") # 환경변수에서 로드
GROUNDING_DINO_PATH = "IDEA-Research/grounding-dino-tiny"