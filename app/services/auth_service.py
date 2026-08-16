from app.repositories.user_repository import UserRepository
from app.core import (
    verify_password, 
    create_access_token, 
    dummy_verify,
    UnauthorizedException
)
from app.schemas.user_schemas import TokenResponse
from app.models.user_model import UserModel

class AuthService:
    """Serviço de autenticação e geração de tokens JWT."""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def authenticate(self, username: str, password: str) -> UserModel:
        """Autentica o usuário validando as credenciais. Lança UnauthorizedException se inválido."""
        user = self.user_repo.get_by_username(username)
        if not user:
            dummy_verify()
            raise UnauthorizedException("Incorrect username or password")
        if not verify_password(password, user.password):
            raise UnauthorizedException("Incorrect username or password")
        return user

    def login(self, username: str, password: str) -> TokenResponse:
        """Realiza login e retorna o TokenResponse com access_token."""
        user = self.authenticate(username, password)
        access_token = create_access_token(user.id)
        return TokenResponse(access_token=access_token, token_type="bearer")
