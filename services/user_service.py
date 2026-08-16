from math import ceil
from typing import Optional
from repositories.user_repository import UserRepository
from models.user_model import UserModel
from schemas.user_schemas import UserCreate, PaginatedUserResponse
from security import get_password_hash
from core.exceptions import UnauthorizedException, BusinessException, ResourceNotFoundException

class UserService:
    """Serviço de domínio responsável pela gestão de usuários."""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def create_user(self, user_in: UserCreate, current_user: UserModel) -> UserModel:
        """Cria um novo usuário no sistema. Exige privilégio de admin."""
        if not current_user.admin:
            raise UnauthorizedException()

        existing = self.user_repo.get_by_username(user_in.username)
        if existing:
            raise BusinessException("Username already registered")

        hashed_password = get_password_hash(user_in.password)
        new_user = UserModel(
            username=user_in.username,
            password=hashed_password,
            admin=bool(user_in.admin)
        )
        return self.user_repo.create(new_user)

    def get_paginated_users(
        self, 
        page: int = 1, 
        limit: int = 10, 
        current_user: Optional[UserModel] = None
    ) -> PaginatedUserResponse:
        """Retorna uma lista paginada de usuários cadastrados. Exige privilégio de admin."""
        if current_user and not current_user.admin:
            raise UnauthorizedException()

        users, total = self.user_repo.get_paginated(page=page, limit=limit)
        total_pages = ceil(total / limit) if limit > 0 else 1

        return PaginatedUserResponse(
            page=page,
            total_pages=total_pages,
            users=users
        )

    def delete_user(self, user_id: int, current_user: UserModel) -> None:
        """Exclui um usuário. Impede a autoexclusão e exige privilégio de admin."""
        if not current_user.admin:
            raise UnauthorizedException()
        if user_id == current_user.id:
            raise UnauthorizedException()

        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundException()

        self.user_repo.delete(user)
