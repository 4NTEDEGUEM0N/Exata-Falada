from pydantic import BaseModel, ConfigDict
from typing import List
from datetime import datetime

class BookResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PaginatedBookResponse(BaseModel):
    page: int
    total_pages: int
    books: List[BookResponse]
