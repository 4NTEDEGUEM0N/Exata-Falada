from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
from security import decode_token, oatuh2_schema
from models.user_model import UserModel
from core.exceptions import UnauthorizedException
from repositories.user_repository import UserRepository
from repositories.task_repository import TaskRepository
from repositories.book_repository import BookRepository
from repositories.library_repository import LibraryRepository
from integrations.storage.base import StorageProvider
from integrations.storage.factory import StorageFactory
from integrations.ai.base import AIProvider
from integrations.ai.factory import AIFactory

# Re-export oauth2_scheme com padrão PEP8 e mantendo retrocompatibilidade
oauth2_scheme = oatuh2_schema

# --- Repositories Injected Providers ---
def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Provedor de injeção de dependência para o UserRepository."""
    return UserRepository(db)

def get_task_repository(db: Session = Depends(get_db)) -> TaskRepository:
    """Provedor de injeção de dependência para o TaskRepository."""
    return TaskRepository(db)

def get_book_repository(db: Session = Depends(get_db)) -> BookRepository:
    """Provedor de injeção de dependência para o BookRepository."""
    return BookRepository(db)

def get_library_repository(db: Session = Depends(get_db)) -> LibraryRepository:
    """Provedor de injeção de dependência para o LibraryRepository."""
    return LibraryRepository(db)

# --- Storage Provider Injected Provider ---
def get_storage_provider() -> StorageProvider:
    """Provedor de injeção de dependência para o StorageProvider ativo."""
    return StorageFactory.get_provider()

# --- AI Provider Injected Provider ---
def get_ai_provider() -> AIProvider:
    """Provedor de injeção de dependência para o AIProvider ativo."""
    return AIFactory.get_provider()


# --- Authentication & Current User ---
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: UserRepository = Depends(get_user_repository)
) -> UserModel:
    """Extrai e valida o token JWT, retornando a entidade UserModel autenticada via UserRepository."""
    payload = decode_token(token)
    if not payload:
        raise UnauthorizedException()
    
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException()
    
    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        raise UnauthorizedException()

    user = user_repo.get_by_id(user_id_int)
    if not user:
        raise UnauthorizedException()
    
    return user

async def get_current_admin(
    current_user: UserModel = Depends(get_current_user)
) -> UserModel:
    """Garante que o usuário autenticado atual possui privilégios de administrador."""
    if not current_user.admin:
        raise UnauthorizedException()
    return current_user
