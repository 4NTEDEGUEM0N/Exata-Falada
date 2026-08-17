import pytest
from unittest.mock import MagicMock
from app.services.task_service import TaskService
from app.models.user_model import UserModel
from app.models.task_model import TaskModel
from app.core.exceptions import ForbiddenException, ResourceNotFoundException

def test_get_all_tasks_non_admin_forbidden():
    mock_repo = MagicMock()
    service = TaskService(mock_repo)
    current_user = UserModel(id=2, username="normal", admin=False)

    with pytest.raises(ForbiddenException):
        service.get_all_tasks(current_user=current_user)

def test_get_user_tasks_forbidden():
    mock_repo = MagicMock()
    service = TaskService(mock_repo)
    current_user = UserModel(id=2, username="normal", admin=False)

    with pytest.raises(ForbiddenException):
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

    with pytest.raises(ForbiddenException):
        service.get_task_by_id(task_id=10, current_user=current_user)

from datetime import datetime

def test_get_all_tasks_success():
    mock_repo = MagicMock()
    now = datetime.now()
    task = TaskModel(id=1, user_id=1, pdf_filename="doc.pdf", status="completed", created_at=now)
    mock_repo.get_all_paginated.return_value = ([task], 1)
    service = TaskService(mock_repo)
    admin_user = UserModel(id=1, username="admin", admin=True)

    res = service.get_all_tasks(current_user=admin_user)
    assert res.total_pages == 1
    assert len(res.tasks) == 1

def test_get_user_tasks_success():
    mock_repo = MagicMock()
    now = datetime.now()
    task = TaskModel(id=1, user_id=2, pdf_filename="doc.pdf", status="completed", created_at=now)
    mock_repo.get_by_user_id_paginated.return_value = ([task], 1)
    service = TaskService(mock_repo)
    normal_user = UserModel(id=2, username="normal", admin=False)

    res = service.get_user_tasks(user_id=2, current_user=normal_user)
    assert res.total_pages == 1

def test_delete_task_success():
    mock_repo = MagicMock()
    task = TaskModel(id=10, user_id=2)
    mock_repo.get_by_id.return_value = task
    service = TaskService(mock_repo)
    normal_user = UserModel(id=2, username="normal", admin=False)

    service.delete_task(task_id=10, current_user=normal_user)
    mock_repo.delete.assert_called_once_with(task)
