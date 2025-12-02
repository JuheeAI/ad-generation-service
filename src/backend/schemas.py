from pydantic import BaseModel, Field, constr, field_validator
import base64
import binascii

class Params(BaseModel):
    brand_name: str | None = None
    background: str | None = None
    target: str | None = None
    size: constr(pattern=r"^\d+x\d+$") = Field("1024x1024", description='"가로x세로" 형식')
    model_alias: str | None = None
    file_saved: bool = False
    seed: int | None = None

class ImageGenerationRequest(BaseModel):
    prompt: str = Field(..., description="프롬프트 문장")
    params: Params
    product_image: str | None = Field(None, description="Base64 인코딩된 제품 이미지")
    model_image: str | None = Field(None, description="Base64 인코딩된 모델 이미지")

    @field_validator("product_image", "model_image")
    @classmethod
    def validate_base64(cls, v: str | None):
        if v is None: return None
        try:
            if ',' in v:
                v = v.split(',', 1)[1]
            missing_padding = len(v) % 4
            if missing_padding:
                v += '=' * (4 - missing_padding)
            base64.b64decode(v, validate=True)
            return v
        except (binascii.Error, IndexError, TypeError) as e:
            raise ValueError(f"Invalid base64 string: {e}")