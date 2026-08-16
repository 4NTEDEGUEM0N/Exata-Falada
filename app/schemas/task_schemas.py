from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum

class TaskStatusEnum(str, Enum):
    CREATED = "Created"
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    COMPLETED_WITH_ERRORS = "Completed with errors"
    ERROR = "Error"

class TaskResponse(BaseModel):
    id: int
    pdf_filename: str
    html_filename: Optional[str] = None
    status: str
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PaginatedTaskResponse(BaseModel):
    page: int
    total_pages: int
    tasks: List[TaskResponse]

class TaskStatusResponse(BaseModel):
    status: str
    progress: int
    logs: Optional[str] = None
    html_filename: Optional[str] = None
