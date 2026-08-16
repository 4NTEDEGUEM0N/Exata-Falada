from fastapi import APIRouter, Depends, status, UploadFile, File
from fastapi.responses import FileResponse
from app.schemas.library_schemas import BookResponse, PaginatedBookResponse
from app.schemas.user_schemas import PaginatedUserResponse
from app.services.library_service import LibraryService
from app.integrations.storage.base import MediaType
from app.api.deps import get_library_service, get_current_user
from app.models.user_model import UserModel
from app.core import settings, BusinessException

library_router = APIRouter(prefix="/library", tags=["library"])

@library_router.get("/", response_model=PaginatedBookResponse)
async def get_all_books(
    page: int = 1,
    current_user: UserModel = Depends(get_current_user),
    library_service: LibraryService = Depends(get_library_service)
):
    """Retorna todos os livros da biblioteca paginados (exige admin)."""
    return library_service.get_all_books(page=page, limit=10, current_user=current_user)

@library_router.post("/", response_model=BookResponse)
async def create_book(
    file: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_user),
    library_service: LibraryService = Depends(get_library_service)
):
    """Faz upload de um livro em formato HTML (exige admin)."""
    if file.content_type != MediaType.HTML.value:
        raise BusinessException("Os arquivos deve ser HTML.")
    
    #if file.size > settings.MAX_FILE_SIZE:
    #    raise BusinessException("Arquivo muito grande. O limite é 50MB.", status_code=413)

    content = (await file.read()).decode("utf-8")
    await file.seek(0)
    return library_service.upload_book(
        file_obj=file.file,
        filename=file.filename or "book.html",
        content=content,
        current_user=current_user
    )

@library_router.post("/add/{user_id}/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_book_to_user(
    user_id: int,
    book_id: int,
    current_user: UserModel = Depends(get_current_user),
    library_service: LibraryService = Depends(get_library_service)
):
    """Associa um livro a um usuário (exige admin)."""
    library_service.add_user_access(user_id=user_id, book_id=book_id, current_user=current_user)

@library_router.post("/remove/{user_id}/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_book_from_user(
    user_id: int,
    book_id: int,
    current_user: UserModel = Depends(get_current_user),
    library_service: LibraryService = Depends(get_library_service)
):
    """Remove a associação de um livro com um usuário (exige admin)."""
    library_service.remove_user_access(user_id=user_id, book_id=book_id, current_user=current_user)

@library_router.get("/books/{user_id}", response_model=PaginatedBookResponse)
async def get_all_user_books(
    user_id: int,
    page: int = 1,
    current_user: UserModel = Depends(get_current_user),
    library_service: LibraryService = Depends(get_library_service)
):
    """Retorna os livros disponíveis para um determinado usuário (dono ou admin)."""
    return library_service.get_user_books(user_id=user_id, page=page, limit=10, current_user=current_user)

@library_router.get("/users/{book_id}", response_model=PaginatedUserResponse)
async def get_all_book_users(
    book_id: int,
    page: int = 1,
    current_user: UserModel = Depends(get_current_user),
    library_service: LibraryService = Depends(get_library_service)
):
    """Retorna os usuários com acesso a um determinado livro (exige admin)."""
    return library_service.get_book_users(book_id=book_id, page=page, limit=10, current_user=current_user)

@library_router.get("/{book_id}")
async def get_book_file(
    book_id: int,
    current_user: UserModel = Depends(get_current_user),
    library_service: LibraryService = Depends(get_library_service)
):
    """Retorna o arquivo HTML do livro para visualização inline (usuário autorizado ou admin)."""
    file_path, filename = library_service.get_book_file(book_id=book_id, current_user=current_user)
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=MediaType.HTML.value,
        content_disposition_type="inline"
    )

@library_router.post("/delete/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: int,
    current_user: UserModel = Depends(get_current_user),
    library_service: LibraryService = Depends(get_library_service)
):
    """Exclui um livro da biblioteca (exige admin)."""
    library_service.delete_book(book_id=book_id, current_user=current_user)
