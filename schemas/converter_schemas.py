from pydantic import BaseModel
from typing import Optional, List
from core import settings

class ConverterRequest(BaseModel):
    paginas: Optional[str] = ""
    dpi: Optional[int] = settings.DEFAULT_DPI
    workers: Optional[int] = settings.DEFAULT_WORKERS
    ai_model: Optional[str] = None
    report_button: Optional[bool] = settings.DEFAULT_REPORT_BUTTON

class ModelsResponse(BaseModel):
    available_models: List[str]
    default_model: str

class ConverterInitResponse(BaseModel):
    task_id: int
    message: str
