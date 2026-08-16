import os
import shutil
from math import ceil
from typing import Tuple, BinaryIO, Optional
from core import (
    settings,
    UnauthorizedException, 
    BusinessException, 
    ResourceNotFoundException,
    sanitize_filename
)
from repositories.book_repository import BookRepository
from repositories.library_repository import LibraryRepository
from repositories.user_repository import UserRepository
from models.book_model import BookModel
from models.user_model import UserModel
from schemas.library_schemas import PaginatedBookResponse
from schemas.user_schemas import PaginatedUserResponse

class LibraryService:
    """Serviço de domínio responsável pela biblioteca de livros e permissões de acesso N:N."""

    def __init__(
        self,
        book_repo: BookRepository,
        library_repo: LibraryRepository,
        user_repo: UserRepository
    ):
        self.book_repo = book_repo
        self.library_repo = library_repo
        self.user_repo = user_repo

    def upload_book(
        self,
        file_obj: BinaryIO,
        filename: str,
        content: str,
        current_user: UserModel
    ) -> BookModel:
        """Valida e persiste um livro HTML na biblioteca. Exige admin."""
        if not current_user.admin:
            raise UnauthorizedException()

        if "</html>" not in content.lower():
            raise BusinessException("Conteúdo HTML inválido no arquivo.")

        sanitized = sanitize_filename(filename)
        file_path = os.path.join(settings.LIBRARY_DIR, sanitized)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file_obj, buffer)

        book = BookModel(filename=sanitized, file_path=file_path)
        return self.book_repo.create(book)

    def get_all_books(
        self, 
        page: int = 1, 
        limit: int = 10, 
        current_user: Optional[UserModel] = None
    ) -> PaginatedBookResponse:
        """Retorna todos os livros cadastrados na biblioteca. Exige admin."""
        if current_user and not current_user.admin:
            raise UnauthorizedException()

        books, total = self.book_repo.get_paginated(page=page, limit=limit)
        total_pages = ceil(total / limit) if limit > 0 else 1

        return PaginatedBookResponse(
            page=page,
            total_pages=total_pages,
            books=books
        )

    def get_user_books(
        self, 
        user_id: int, 
        page: int = 1, 
        limit: int = 10, 
        current_user: Optional[UserModel] = None
    ) -> PaginatedBookResponse:
        """Retorna os livros liberados para um usuário."""
        if current_user and user_id != current_user.id and not current_user.admin:
            raise UnauthorizedException()

        books, total = self.library_repo.get_user_books_paginated(user_id=user_id, page=page, limit=limit)
        total_pages = ceil(total / limit) if limit > 0 else 1

        return PaginatedBookResponse(
            page=page,
            total_pages=total_pages,
            books=books
        )

    def get_book_users(
        self, 
        book_id: int, 
        page: int = 1, 
        limit: int = 10, 
        current_user: Optional[UserModel] = None
    ) -> PaginatedUserResponse:
        """Retorna os usuários que têm acesso a um livro. Exige admin."""
        if current_user and not current_user.admin:
            raise UnauthorizedException()

        users, total = self.library_repo.get_book_users_paginated(book_id=book_id, page=page, limit=limit)
        total_pages = ceil(total / limit) if limit > 0 else 1

        return PaginatedUserResponse(
            page=page,
            total_pages=total_pages,
            users=users
        )

    def add_user_access(self, user_id: int, book_id: int, current_user: UserModel) -> None:
        """Associa um livro a um usuário. Exige admin."""
        if not current_user.admin:
            raise UnauthorizedException()

        self.library_repo.add_association(user_id=user_id, book_id=book_id)

    def remove_user_access(self, user_id: int, book_id: int, current_user: UserModel) -> None:
        """Remove o acesso de um usuário a um livro. Exige admin."""
        if not current_user.admin:
            raise UnauthorizedException()

        removed = self.library_repo.remove_association(user_id=user_id, book_id=book_id)
        if not removed:
            raise ResourceNotFoundException()

    def get_book_file(self, book_id: int, current_user: UserModel) -> Tuple[str, str]:
        """Verifica a permissão e retorna (file_path, filename) para entrega do arquivo."""
        book = self.book_repo.get_by_id(book_id)
        if not book:
            raise ResourceNotFoundException()

        if not current_user.admin and not self.library_repo.has_user_access(current_user.id, book_id):
            raise UnauthorizedException()

        return book.file_path, book.filename

    def delete_book(self, book_id: int, current_user: UserModel) -> None:
        """Exclui um livro e suas associações da biblioteca. Exige admin."""
        if not current_user.admin:
            raise UnauthorizedException()

        book = self.book_repo.get_by_id(book_id)
        if not book:
            raise ResourceNotFoundException()

        self.book_repo.delete(book)
