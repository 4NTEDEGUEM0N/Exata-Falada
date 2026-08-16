from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc
from models.library_model import LibraryModel
from models.book_model import BookModel
from models.user_model import UserModel
from .base_repository import BaseRepository

class LibraryRepository(BaseRepository[LibraryModel]):
    """Repositório responsável pelo relacionamento de associação entre Usuários e Livros (LibraryModel)."""
    
    def __init__(self, db: Session):
        super().__init__(LibraryModel, db)

    def get_association(self, user_id: int, book_id: int) -> Optional[LibraryModel]:
        """Busca o registro de associação entre um usuário e um livro."""
        return self.db.query(LibraryModel).filter(
            LibraryModel.user_id == user_id, 
            LibraryModel.book_id == book_id
        ).first()

    def add_association(self, user_id: int, book_id: int) -> LibraryModel:
        """Associa um livro a um usuário."""
        existing = self.get_association(user_id, book_id)
        if existing:
            return existing
        association = LibraryModel(user_id=user_id, book_id=book_id)
        return self.create(association)

    def remove_association(self, user_id: int, book_id: int) -> bool:
        """Remove a associação de um livro com um usuário. Retorna True se removido, False se não existia."""
        association = self.get_association(user_id, book_id)
        if not association:
            return False
        self.delete(association)
        return True

    def has_user_access(self, user_id: int, book_id: int) -> bool:
        """Verifica se o usuário possui acesso ao livro especificado."""
        return self.get_association(user_id, book_id) is not None

    def get_user_books_paginated(
        self, 
        user_id: int, 
        page: int = 1, 
        limit: int = 10
    ) -> Tuple[List[BookModel], int]:
        """Retorna a lista paginada de livros associados a um usuário e o total."""
        skip = max(0, (page - 1) * limit)
        base_query = (
            self.db.query(BookModel)
            .join(LibraryModel, BookModel.id == LibraryModel.book_id)
            .filter(LibraryModel.user_id == user_id)
            .order_by(desc(BookModel.id))
        )
        total_count = base_query.count()
        books = base_query.offset(skip).limit(limit).all()
        return books, total_count

    def get_book_users_paginated(
        self, 
        book_id: int, 
        page: int = 1, 
        limit: int = 10
    ) -> Tuple[List[UserModel], int]:
        """Retorna a lista paginada de usuários que possuem acesso a um livro e o total."""
        skip = max(0, (page - 1) * limit)
        base_query = (
            self.db.query(UserModel)
            .join(LibraryModel, UserModel.id == LibraryModel.user_id)
            .filter(LibraryModel.book_id == book_id)
            .order_by(desc(UserModel.id))
        )
        total_count = base_query.count()
        users = base_query.offset(skip).limit(limit).all()
        return users, total_count
