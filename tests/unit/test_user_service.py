import pytest
from unittest.mock import MagicMock
from app.services.user_service import UserService
from app.models.user_model import UserModel
from app.schemas.user_schemas import UserCreate
from app.core.exceptions import UnauthorizedException, BusinessException, ResourceNotFoundException

def test_create_user_non_admin_forbidden():
    mock_repo = MagicMock()
    service = UserService(mock_repo)
    user_in = UserCreate(username="user1", password="123")
    current_user = UserModel(id=2, username="normal", admin=False)

    with pytest.raises(UnauthorizedException):
        service.create_user(user_in, current_user)

def test_create_user_duplicate_username():
    mock_repo = MagicMock()
    mock_repo.get_by_username.return_value = UserModel(id=3, username="existing")
    service = UserService(mock_repo)
    user_in = UserCreate(username="existing", password="123")
    current_user = UserModel(id=1, username="admin", admin=True)

    with pytest.raises(BusinessException) as exc_info:
        service.create_user(user_in, current_user)
    assert exc_info.value.detail == "Username already registered"

def test_create_user_success():
    mock_repo = MagicMock()
    mock_repo.get_by_username.return_value = None
    mock_repo.create.side_effect = lambda u: u

    service = UserService(mock_repo)
    user_in = UserCreate(username="newuser", password="secretpassword", admin=False)
    current_user = UserModel(id=1, username="admin", admin=True)

    created = service.create_user(user_in, current_user)
    assert created.username == "newuser"
    assert created.admin is False
    assert created.password != "secretpassword"  # hashed

def test_get_paginated_users():
    mock_repo = MagicMock()
    mock_repo.get_paginated.return_value = ([UserModel(id=1, username="a", admin=False)], 25)
    service = UserService(mock_repo)
    current_user = UserModel(id=1, username="admin", admin=True)

    result = service.get_paginated_users(page=1, limit=10, current_user=current_user)
    assert result.page == 1
    assert result.total_pages == 3
    assert len(result.users) == 1

def test_delete_user_self_forbidden():
    mock_repo = MagicMock()
    service = UserService(mock_repo)
    current_user = UserModel(id=1, username="admin", admin=True)

    with pytest.raises(UnauthorizedException):
        service.delete_user(user_id=1, current_user=current_user)

def test_delete_user_not_found():
    mock_repo = MagicMock()
    mock_repo.get_by_id.return_value = None
    service = UserService(mock_repo)
    current_user = UserModel(id=1, username="admin", admin=True)

    with pytest.raises(ResourceNotFoundException):
        service.delete_user(user_id=999, current_user=current_user)
