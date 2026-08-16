import pytest
from unittest.mock import MagicMock
from app.services.converter_service import ConverterService
from app.models.user_model import UserModel
from app.models.task_model import TaskModel
from app.schemas.task_schemas import TaskStatusEnum
from app.schemas.converter_schemas import ConverterRequest
from app.core.exceptions import BusinessException, ResourceNotFoundException, UnauthorizedException

def test_initiate_conversion_invalid_type():
    mock_task_repo = MagicMock()
    mock_storage = MagicMock()
    mock_ai = MagicMock()
    mock_pdf = MagicMock()
    mock_html = MagicMock()
    service = ConverterService(mock_task_repo, mock_storage, mock_ai, mock_pdf, mock_html)

    mock_file = MagicMock()
    mock_file.content_type = "text/plain"
    mock_user = UserModel(id=1, username="test", admin=False)

    with pytest.raises(BusinessException):
        service.initiate_conversion(mock_file, ConverterRequest(), mock_user, MagicMock())

def test_get_task_download_info_not_ready():
    mock_task_repo = MagicMock()
    task = TaskModel(id=1, user_id=1, status=TaskStatusEnum.PROCESSING.value)
    mock_task_repo.get_by_id.return_value = task

    service = ConverterService(mock_task_repo, MagicMock(), MagicMock(), MagicMock(), MagicMock())
    user = UserModel(id=1, username="test", admin=False)

    with pytest.raises(BusinessException) as exc_info:
        service.get_task_download_info(task_id=1, current_user=user)
    assert "Arquivo ainda não está pronto" in exc_info.value.detail

def test_get_task_status_unauthorized():
    mock_task_repo = MagicMock()
    task = TaskModel(id=1, user_id=2, status=TaskStatusEnum.COMPLETED.value)
    mock_task_repo.get_by_id.return_value = task

    service = ConverterService(mock_task_repo, MagicMock(), MagicMock(), MagicMock(), MagicMock())
    user = UserModel(id=3, username="other", admin=False)

    with pytest.raises(UnauthorizedException):
        service.get_task_status(task_id=1, current_user=user)
