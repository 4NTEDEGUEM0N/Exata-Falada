import pytest
from unittest.mock import MagicMock, patch
from app.api.deps import (
    get_user_repository,
    get_task_repository,
    get_book_repository,
    get_library_repository,
    get_storage_provider,
    get_ai_provider,
    get_pdf_service,
    get_patcher_service,
    get_html_service,
    get_auth_service,
    get_user_service,
    get_task_service,
    get_library_service,
    get_converter_service,
    get_current_user,
    get_current_admin
)
from app.models.user_model import UserModel
from app.core import UnauthorizedException


def test_deps_factories():
    mock_db = MagicMock()
    
    assert get_user_repository(mock_db) is not None
    assert get_task_repository(mock_db) is not None
    assert get_book_repository(mock_db) is not None
    assert get_library_repository(mock_db) is not None

    get_storage_provider.cache_clear()
    get_ai_provider.cache_clear()

    with patch("app.integrations.storage.factory.StorageFactory.get_provider") as mock_sp:
        mock_instance = MagicMock()
        mock_sp.return_value = mock_instance
        res1 = get_storage_provider()
        res2 = get_storage_provider()
        assert res1 is res2
        assert mock_sp.call_count == 1

    with patch("app.integrations.ai.factory.AIFactory.get_provider") as mock_ai:
        mock_ai_inst = MagicMock()
        mock_ai.return_value = mock_ai_inst
        res_ai1 = get_ai_provider()
        res_ai2 = get_ai_provider()
        assert res_ai1 is res_ai2
        assert mock_ai.call_count == 1

    assert get_pdf_service() is not None
    assert get_patcher_service() is not None
    assert get_html_service() is not None

    mock_user_repo = MagicMock()
    mock_task_repo = MagicMock()
    mock_book_repo = MagicMock()
    mock_lib_repo = MagicMock()

    assert get_auth_service(mock_user_repo) is not None
    assert get_user_service(mock_user_repo) is not None
    assert get_task_service(mock_task_repo) is not None
    assert get_library_service(mock_book_repo, mock_lib_repo, mock_user_repo) is not None
    assert get_converter_service(mock_task_repo, MagicMock(), MagicMock(), MagicMock(), MagicMock()) is not None


@pytest.mark.anyio
async def test_get_current_user_success():
    mock_user_repo = MagicMock()
    user = UserModel(id=1, username="test", admin=False)
    mock_user_repo.get_by_id.return_value = user

    with patch("app.api.deps.decode_token", return_value={"sub": "1"}):
        res = await get_current_user(token="valid_token", user_repo=mock_user_repo)
        assert res.id == 1
        assert res.username == "test"

@pytest.mark.anyio
async def test_get_current_user_invalid_token():
    with patch("app.api.deps.decode_token", return_value=None):
        with pytest.raises(UnauthorizedException):
            await get_current_user(token="invalid_token", user_repo=MagicMock())

@pytest.mark.anyio
async def test_get_current_user_missing_sub():
    with patch("app.api.deps.decode_token", return_value={}):
        with pytest.raises(UnauthorizedException):
            await get_current_user(token="token_without_sub", user_repo=MagicMock())

@pytest.mark.anyio
async def test_get_current_user_empty_sub():
    with patch("app.api.deps.decode_token", return_value={"sub": ""}):
        with pytest.raises(UnauthorizedException):
            await get_current_user(token="token_with_empty_sub", user_repo=MagicMock())

@pytest.mark.anyio
async def test_get_current_user_non_integer_sub():
    with patch("app.api.deps.decode_token", return_value={"sub": "abc"}):
        with pytest.raises(UnauthorizedException):
            await get_current_user(token="bad_sub", user_repo=MagicMock())

@pytest.mark.anyio
async def test_get_current_user_not_found_in_db():
    mock_user_repo = MagicMock()
    mock_user_repo.get_by_id.return_value = None

    with patch("app.api.deps.decode_token", return_value={"sub": "999"}):
        with pytest.raises(UnauthorizedException):
            await get_current_user(token="nonexistent_user", user_repo=mock_user_repo)

@pytest.mark.anyio
async def test_get_current_admin_success():
    admin_user = UserModel(id=1, username="admin", admin=True)
    res = await get_current_admin(current_user=admin_user)
    assert res.admin is True

from app.core import UnauthorizedException, ForbiddenException

@pytest.mark.anyio
async def test_get_current_admin_forbidden():
    normal_user = UserModel(id=2, username="normal", admin=False)
    with pytest.raises(ForbiddenException):
        await get_current_admin(current_user=normal_user)
