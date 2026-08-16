from fastapi import Depends
from sqlalchemy.orm import Session
from core import (
    get_db, 
    decode_token, 
    oauth2_scheme, 
    UnauthorizedException
)
from models.user_model import UserModel
from repositories.user_repository import UserRepository
from repositories.task_repository import TaskRepository
from repositories.book_repository import BookRepository
from repositories.library_repository import LibraryRepository
from integrations.storage.base import StorageProvider
from integrations.storage.factory import StorageFactory
from integrations.ai.base import AIProvider
from integrations.ai.factory import AIFactory
from services.pdf_service import PdfService
from services.patcher_service import PatcherService
from services.html_service import HtmlService
from services.auth_service import AuthService
from services.user_service import UserService
from services.task_service import TaskService
from services.library_service import LibraryService
from services.converter_service import ConverterService

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

# --- Services Injected Providers ---
def get_pdf_service() -> PdfService:
    """Provedor de injeção de dependência para o PdfService."""
    return PdfService()

def get_patcher_service() -> PatcherService:
    """Provedor de injeção de dependência para o PatcherService."""
    return PatcherService()

def get_html_service() -> HtmlService:
    """Provedor de injeção de dependência para o HtmlService."""
    return HtmlService()

def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository)
) -> AuthService:
    """Provedor de injeção de dependência para o AuthService."""
    return AuthService(user_repo)

def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository)
) -> UserService:
    """Provedor de injeção de dependência para o UserService."""
    return UserService(user_repo)

def get_task_service(
    task_repo: TaskRepository = Depends(get_task_repository)
) -> TaskService:
    """Provedor de injeção de dependência para o TaskService."""
    return TaskService(task_repo)

def get_library_service(
    book_repo: BookRepository = Depends(get_book_repository),
    library_repo: LibraryRepository = Depends(get_library_repository),
    user_repo: UserRepository = Depends(get_user_repository)
) -> LibraryService:
    """Provedor de injeção de dependência para o LibraryService."""
    return LibraryService(book_repo, library_repo, user_repo)

def get_converter_service(
    task_repo: TaskRepository = Depends(get_task_repository),
    storage_provider: StorageProvider = Depends(get_storage_provider),
    ai_provider: AIProvider = Depends(get_ai_provider),
    pdf_service: PdfService = Depends(get_pdf_service),
    html_service: HtmlService = Depends(get_html_service)
) -> ConverterService:
    """Provedor de injeção de dependência para o ConverterService."""
    return ConverterService(
        task_repo=task_repo,
        storage_provider=storage_provider,
        ai_provider=ai_provider,
        pdf_service=pdf_service,
        html_service=html_service
    )


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
