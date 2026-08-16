import pytest
from unittest.mock import MagicMock, patch
from services.auth_service import AuthService
from models.user_model import UserModel
from core.exceptions import UnauthorizedException
from security import get_password_hash

def test_auth_service_authenticate_success():
    mock_repo = MagicMock()
    hashed = get_password_hash("secret123")
    user = UserModel(id=1, username="thiago", password=hashed, admin=True)
    mock_repo.get_by_username.return_value = user

    service = AuthService(mock_repo)
    result = service.authenticate("thiago", "secret123")
    assert result.id == 1
    assert result.username == "thiago"

def test_auth_service_authenticate_wrong_password():
    mock_repo = MagicMock()
    hashed = get_password_hash("secret123")
    user = UserModel(id=1, username="thiago", password=hashed, admin=True)
    mock_repo.get_by_username.return_value = user

    service = AuthService(mock_repo)
    with pytest.raises(UnauthorizedException):
        service.authenticate("thiago", "wrong_pass")

def test_auth_service_authenticate_user_not_found():
    mock_repo = MagicMock()
    mock_repo.get_by_username.return_value = None

    service = AuthService(mock_repo)
    with pytest.raises(UnauthorizedException):
        service.authenticate("nonexistent", "secret123")

def test_auth_service_login_returns_token():
    mock_repo = MagicMock()
    hashed = get_password_hash("secret123")
    user = UserModel(id=1, username="thiago", password=hashed, admin=True)
    mock_repo.get_by_username.return_value = user

    service = AuthService(mock_repo)
    token_resp = service.login("thiago", "secret123")
    assert token_resp.token_type == "bearer"
    assert isinstance(token_resp.access_token, str)
