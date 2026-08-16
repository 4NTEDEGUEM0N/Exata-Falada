from math import ceil
from typing import Optional
from app.repositories.task_repository import TaskRepository
from app.models.task_model import TaskModel
from app.models.user_model import UserModel
from app.schemas.task_schemas import PaginatedTaskResponse
from app.core.exceptions import UnauthorizedException, ResourceNotFoundException

class TaskService:
    """Serviço de domínio responsável pelo ciclo de vida e consultas de tarefas."""

    def __init__(self, task_repo: TaskRepository):
        self.task_repo = task_repo

    def get_all_tasks(
        self, 
        page: int = 1, 
        limit: int = 10, 
        current_user: Optional[UserModel] = None
    ) -> PaginatedTaskResponse:
        """Retorna todas as tarefas paginadas. Exige privilégio de admin."""
        if current_user and not current_user.admin:
            raise UnauthorizedException()

        tasks, total = self.task_repo.get_all_paginated(page=page, limit=limit)
        total_pages = ceil(total / limit) if limit > 0 else 1

        return PaginatedTaskResponse(
            page=page,
            total_pages=total_pages,
            tasks=tasks
        )

    def get_user_tasks(
        self, 
        user_id: int, 
        page: int = 1, 
        limit: int = 10, 
        current_user: Optional[UserModel] = None
    ) -> PaginatedTaskResponse:
        """Retorna as tarefas de um usuário específico paginadas. Valida se é o próprio usuário ou admin."""
        if current_user and user_id != current_user.id and not current_user.admin:
            raise UnauthorizedException()

        tasks, total = self.task_repo.get_by_user_id_paginated(user_id=user_id, page=page, limit=limit)
        total_pages = ceil(total / limit) if limit > 0 else 1

        return PaginatedTaskResponse(
            page=page,
            total_pages=total_pages,
            tasks=tasks
        )

    def get_task_by_id(self, task_id: int, current_user: UserModel) -> TaskModel:
        """Busca uma tarefa por ID com validação de permissão (dono ou admin)."""
        task = self.task_repo.get_by_id(task_id)
        if not task:
            raise ResourceNotFoundException()

        if task.user_id != current_user.id and not current_user.admin:
            raise UnauthorizedException()

        return task

    def delete_task(self, task_id: int, current_user: UserModel) -> None:
        """Exclui uma tarefa com validação de permissão."""
        task = self.get_task_by_id(task_id, current_user)
        self.task_repo.delete(task)
