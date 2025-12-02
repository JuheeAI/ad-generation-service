from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session
from typing import List, Optional
from pydantic import BaseModel

from .. import crud, models, schemas
from ..database import get_session
from .auth import get_current_user
from ..services.text_engine import generate_ad_content_logic 

router = APIRouter(prefix="/generations", tags=["Generations"])

# ===================================================
# 순환 참조 없이 모델을 가져오는 의존성 함수
# ===================================================
def get_image_pipeline(request: Request):
    """
    main.py가 시작될 때 app.state.image_pipeline에 저장해둔 모델을 가져옵니다.
    """
    # app.state에 모델이 없으면 아직 로딩 중이라는 뜻
    if not hasattr(request.app.state, "image_pipeline") or not request.app.state.image_pipeline:
        raise HTTPException(status_code=503, detail="AI Models are still loading... Please wait.")
    return request.app.state.image_pipeline

# ---------------------------------------------------
# 1. 텍스트 생성 API (New)
# ---------------------------------------------------
class TextGenRequest(BaseModel):
    product: str
    tone: str = "친근한"
    channel: str = "instagram"
    target_audience: Optional[str] = None
    translate_en: bool = False
    location: Optional[str] = None

@router.post("/text/create")
async def generate_text_api(req: TextGenRequest):
    try:
        # 텍스트 엔진 함수 호출 (CPU 작업이므로 쓰레드풀 필요없을 수 있으나 안전하게)
        result_text = await run_in_threadpool(
            generate_ad_content_logic,
            product_desc=req.product,
            tone=req.tone,
            channel=req.channel,
            target_audience=req.target_audience,
            translate_en=req.translate_en,
            location=req.location
        )
        return {"text": result_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text generation failed: {e}")

# ---------------------------------------------------
# 2. 이미지 생성 API (Refactored)
# ---------------------------------------------------
@router.post("/image/create")
async def generate_image_api(
    request: schemas.ImageGenerationRequest,
    pipeline = Depends(get_image_pipeline) # [사용] 위에서 정의한 함수를 주입
):
    try:
        # A6000 GPU 파이프라인 실행
        # Pydantic v2 호환성을 위해 .model_dump() 사용
        input_data = request.model_dump()
        result = await run_in_threadpool(pipeline.run, input_data)
        return result # {"status": "success", "image_base64": ...}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {e}")

# ---------------------------------------------------
# 3. 결과 저장 및 조회 (기존 CRUD)
# ---------------------------------------------------
@router.post("/", response_model=models.GenerationResponse)
def create_new_generation_record(
    generation: models.GenerationCreate, 
    db: Session = Depends(get_session),
    current_user: models.User = Depends(get_current_user)
):
    return crud.create_generation(db=db, generation=generation, user_id=current_user.id)

@router.get("/", response_model=List[models.GenerationResponse])
def read_all_generations(
    skip: int = 0, limit: int = 100, 
    db: Session = Depends(get_session),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_generations(db, user_id=current_user.id, skip=skip, limit=limit)

@router.delete("/{generation_id}")
def delete_gen(generation_id: int, db: Session = Depends(get_session), current_user: models.User = Depends(get_current_user)):
    crud.delete_generation(db, generation_id, current_user.id)
    return {"ok": True}