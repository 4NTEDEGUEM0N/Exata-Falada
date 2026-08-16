from pydantic import BaseModel
from typing import Optional, List
from config import settings
from .task_schemas import TaskStatusEnum

class ConverterRequest(BaseModel):
    paginas: Optional[str] = ""
    dpi: Optional[int] = settings.DEFAULT_DPI
    gemini_workers: Optional[int] = settings.DEFAULT_GEMINI_WORKERS
    gemini_model: Optional[str] = settings.DEFAULT_MODEL
    report_button: Optional[bool] = settings.DEFAULT_REPORT_BUTTON

class ModelsResponse(BaseModel):
    available_models: List[str]
    default_model: str

class ConverterInitResponse(BaseModel):
    task_id: int
    message: str
