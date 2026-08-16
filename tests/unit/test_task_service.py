import pytest
from unittest.mock import MagicMock
from app.services.task_service import TaskService
from app.models.user_model import UserModel
from app.models.task_model import TaskModel
from app.core.exceptions import UnauthorizedException, ResourceNotFoundException

def test_get_all_tasks_non_admin_forbidden():
    mock_repo = MagicMock()
    service = TaskService(mock_repo)
    current_user = UserModel(id=2, username="normal", admin=False)

    with pytest.raises(UnauthorizedException):
        service.get_all_tasks(current_user=current_user)

def test_get_user_tasks_forbidden():
    mock_repo = MagicMock()
    service = TaskService(mock_repo)
    current_user = UserModel(id=2, username="normal", admin=False)

    with pytest.raises(UnauthorizedException):
        service.get_user_tasks(user_id=1, current_user=current_user)

def test_get_task_by_id_not_found():
    mock_repo = MagicMock()
    mock_repo.get_by_id.return_value = None
    service = TaskService(mock_repo)
    current_user = UserModel(id=1, username="admin", admin=True)

    with pytest.raises(ResourceNotFoundException):
        service.get_task_by_id(task_id=99, current_user=current_user)

def test_get_task_by_id_unauthorized():
    mock_repo = MagicMock()
    task = TaskModel(id=10, user_id=1)
    mock_repo.get_by_id.return_value = task
    service = TaskService(mock_repo)
    current_user = UserModel(id=2, username="other", admin=False)

    with pytest.raises(UnauthorizedException):
        service.get_task_by_id(task_id=10, current_user=current_user)
