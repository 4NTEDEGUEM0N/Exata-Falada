from math import ceil
from app.repositories.task_repository import TaskRepository
from app.models.task_model import TaskModel
from app.models.user_model import UserModel
from app.schemas.task_schemas import PaginatedTaskResponse
from app.core.exceptions import ForbiddenException, ResourceNotFoundException

class TaskService:
    """Serviço de domínio responsável pelo ciclo de vida e consultas de tarefas."""

    def __init__(self, task_repo: TaskRepository):
        self.task_repo = task_repo

    def get_all_tasks(
        self, 
        current_user: UserModel,
        page: int = 1, 
        limit: int = 10
    ) -> PaginatedTaskResponse:
        """Retorna todas as tarefas paginadas. Exige privilégio de admin."""
        if not current_user.admin:
            raise ForbiddenException("Acesso restrito a administradores.")

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
        current_user: UserModel,
        page: int = 1, 
        limit: int = 10
    ) -> PaginatedTaskResponse:
        """Retorna as tarefas de um usuário específico paginadas. Valida se é o próprio usuário ou admin."""
        if user_id != current_user.id and not current_user.admin:
            raise ForbiddenException("Sem permissão para visualizar tarefas de outros usuários.")

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
            raise ResourceNotFoundException("Tarefa não encontrada.")

        if task.user_id != current_user.id and not current_user.admin:
            raise ForbiddenException("Sem permissão para acessar esta tarefa.")

        return task

    def delete_task(self, task_id: int, current_user: UserModel) -> None:
        """Exclui uma tarefa com validação de permissão."""
        task = self.get_task_by_id(task_id, current_user)
        self.task_repo.delete(task)
