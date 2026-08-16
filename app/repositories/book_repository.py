from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.book_model import BookModel
from .base_repository import BaseRepository

class BookRepository(BaseRepository[BookModel]):
    """Repositório responsável pelo acesso aos dados da entidade BookModel."""
    
    def __init__(self, db: Session):
        super().__init__(BookModel, db)

    def get_paginated(self, page: int = 1, limit: int = 10) -> Tuple[List[BookModel], int]:
        """Retorna todos os livros paginados por ordem decrescente de ID e o total geral."""
        skip = max(0, (page - 1) * limit)
        base_query = self.db.query(BookModel).order_by(desc(BookModel.id))
        total_count = base_query.count()
        books = base_query.offset(skip).limit(limit).all()
        return books, total_count
