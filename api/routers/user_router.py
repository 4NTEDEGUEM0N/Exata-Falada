from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from schemas.user_schemas import UserCreate, UserResponse, TokenResponse, PaginatedUserResponse
from services.auth_service import AuthService
from services.user_service import UserService
from api.deps import get_auth_service, get_user_service, get_current_user
from models.user_model import UserModel

user_router = APIRouter(prefix="/user", tags=["user"])

@user_router.post("/token", response_model=TokenResponse)
async def login_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Autentica o usuário e retorna o token JWT."""
    return auth_service.login(form_data.username, form_data.password)

@user_router.post("/signup", response_model=UserResponse)
async def create_user(
    user_schema: UserCreate,
    current_user: UserModel = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Cria um novo usuário (exige admin)."""
    return user_service.create_user(user_schema, current_user)

@user_router.get("/", response_model=PaginatedUserResponse)
async def get_all_users(
    page: int = 1,
    current_user: UserModel = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Retorna a lista paginada de usuários (exige admin)."""
    return user_service.get_paginated_users(page=page, limit=10, current_user=current_user)

@user_router.get("/me", response_model=UserResponse)
async def read_user_me(
    current_user: UserModel = Depends(get_current_user)
):
    """Retorna os dados do usuário autenticado atual."""
    return current_user

@user_router.post("/delete/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Exclui um usuário do sistema (exige admin)."""
    user_service.delete_user(user_id, current_user)
