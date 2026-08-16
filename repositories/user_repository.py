from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc
from models.user_model import UserModel
from .base_repository import BaseRepository

class UserRepository(BaseRepository[UserModel]):
    """Repositório responsável pelo acesso aos dados da entidade UserModel."""
    
    def __init__(self, db: Session):
        super().__init__(UserModel, db)

    def get_by_username(self, username: str) -> Optional[UserModel]:
        """Busca um usuário pelo nome de usuário único."""
        return self.db.query(UserModel).filter(UserModel.username == username).first()

    def get_paginated(self, page: int = 1, limit: int = 10) -> Tuple[List[UserModel], int]:
        """Retorna uma lista paginada de usuários ordenados por ID decrescente e o total geral."""
        skip = max(0, (page - 1) * limit)
        base_query = self.db.query(UserModel).order_by(desc(UserModel.id))
        total_count = base_query.count()
        users = base_query.offset(skip).limit(limit).all()
        return users, total_count

    def get_first_admin(self) -> Optional[UserModel]:
        """Retorna o primeiro usuário com perfil de administrador."""
        return self.db.query(UserModel).filter(UserModel.admin == True).first()
