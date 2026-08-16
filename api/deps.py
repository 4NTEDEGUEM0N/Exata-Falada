from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
from security import decode_token, oatuh2_schema
from models.user_model import UserModel
from core.exceptions import UnauthorizedException

# Re-export oauth2_scheme com padrão PEP8 e mantendo retrocompatibilidade
oauth2_scheme = oatuh2_schema

async def get_current_user(
    db: Session = Depends(get_db), 
    token: str = Depends(oauth2_scheme)
) -> UserModel:
    """Extrai e valida o token JWT, retornando a entidade UserModel autenticada."""
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

    user = db.get(UserModel, user_id_int)
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
