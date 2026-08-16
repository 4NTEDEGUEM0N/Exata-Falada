import pytest
from unittest.mock import MagicMock
from app.repositories.base_repository import BaseRepository
from app.repositories.task_repository import TaskRepository
from app.models.task_model import TaskModel
from app.schemas.task_schemas import TaskStatusEnum


def test_base_repository_operations():
    mock_db = MagicMock()
    repo = BaseRepository(TaskModel, mock_db)

    # get_all
    repo.get_all()
    mock_db.query.assert_called_with(TaskModel)

    # create
    task = TaskModel(id=1)
    repo.create(task)
    mock_db.add.assert_called_with(task)
    mock_db.commit.assert_called()
    mock_db.refresh.assert_called_with(task)

    # delete
    repo.delete(task)
    mock_db.delete.assert_called_with(task)

    # commit & refresh
    repo.commit()
    repo.refresh(task)


def test_task_repository_pagination():
    mock_db = MagicMock()
    repo = TaskRepository(mock_db)

    # get_all_paginated
    tasks, count = repo.get_all_paginated(page=1, limit=10)
    assert mock_db.query.called

    # get_by_user_id_paginated
    tasks, count = repo.get_by_user_id_paginated(user_id=5, page=1, limit=10)
    assert mock_db.query.called


def test_task_repository_update_status():
    mock_db = MagicMock()
    task = TaskModel(id=1, status=TaskStatusEnum.CREATED.value)
    mock_db.get.return_value = task
    repo = TaskRepository(mock_db)

    updated = repo.update_status(1, TaskStatusEnum.PROCESSING.value)
    assert updated.status == TaskStatusEnum.PROCESSING.value

    # task not found
    mock_db.get.return_value = None
    assert repo.update_status(999, TaskStatusEnum.ERROR.value) is None


def test_task_repository_append_log_and_progress():
    mock_db = MagicMock()
    task = TaskModel(id=1, logs="initial log\n", progress=10)
    mock_db.get.return_value = task
    repo = TaskRepository(mock_db)

    updated = repo.append_log_and_progress(1, "step completed", increment_progress=20)
    assert "step completed" in updated.logs
    assert updated.progress == 30

    # without increment
    updated2 = repo.append_log_and_progress(1, "another log", increment_progress=0)
    assert "another log" in updated2.logs
    assert updated2.progress == 30

    # task not found
    mock_db.get.return_value = None
    assert repo.append_log_and_progress(999, "log") is None


def test_task_repository_update_completion():
    mock_db = MagicMock()
    task = TaskModel(id=1, status=TaskStatusEnum.PROCESSING.value, progress=50)
    mock_db.get.return_value = task
    repo = TaskRepository(mock_db)

    updated = repo.update_completion(1, TaskStatusEnum.COMPLETED.value, "output.html", progress=100)
    assert updated.status == TaskStatusEnum.COMPLETED.value
    assert updated.html_filename == "output.html"
    assert updated.progress == 100

    # task not found
    mock_db.get.return_value = None
    assert repo.update_completion(999, TaskStatusEnum.COMPLETED.value, "out.html") is None
