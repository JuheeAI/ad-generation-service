from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .database import create_db_and_tables
from .routers import auth, generations, user_models
from .services.image_engine import ImageGenerationPipeline
from .core import config
import logging

logger = logging.getLogger("uvicorn")
image_pipeline = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global image_pipeline
    logger.info("🚀 Server Start: Loading Models on RTX A6000...")
    create_db_and_tables()
    try:
        image_pipeline = ImageGenerationPipeline(config=config, logger=logger)
        app.state.image_pipeline = image_pipeline
        logger.info("✅ Models Loaded Successfully!")
    except Exception as e:
        logger.error(f"❌ Model Load Failed: {e}")
    yield
    if image_pipeline:
        image_pipeline.model_manager.unload()

app = FastAPI(title="AdGen Monolith API", lifespan=lifespan)

# 정적 파일 마운트 (이미지 서빙용)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)
app.include_router(generations.router)
app.include_router(user_models.router)

@app.get("/")
def health_check():
    return {"status": "ready" if image_pipeline else "loading"}

def get_image_pipeline():
    if not image_pipeline:
        raise RuntimeError("Models are still loading...")
    return image_pipeline