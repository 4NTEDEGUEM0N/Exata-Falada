from fastapi import APIRouter, Depends, status
from app.schemas.task_schemas import TaskResponse, PaginatedTaskResponse
from app.services.task_service import TaskService
from app.api.deps import get_task_service, get_current_user, get_current_admin
from app.models.user_model import UserModel

task_router = APIRouter(prefix="/task", tags=["task"])

@task_router.get("/", response_model=PaginatedTaskResponse)
async def get_all_tasks(
    page: int = 1,
    current_user: UserModel = Depends(get_current_admin),
    task_service: TaskService = Depends(get_task_service)
):
    """Retorna todas as tarefas paginadas (exige admin)."""
    return task_service.get_all_tasks(page=page, limit=10, current_user=current_user)

@task_router.get("/user/{user_id}", response_model=PaginatedTaskResponse)
async def get_all_user_tasks(
    user_id: int,
    page: int = 1,
    current_user: UserModel = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
):
    """Retorna as tarefas de um usuário específico paginadas (dono ou admin)."""
    return task_service.get_user_tasks(user_id=user_id, page=page, limit=10, current_user=current_user)

@task_router.get("/{task_id}", response_model=TaskResponse)
async def get_task_by_id(
    task_id: int,
    current_user: UserModel = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
):
    """Retorna os detalhes de uma tarefa por ID (dono ou admin)."""
    return task_service.get_task_by_id(task_id=task_id, current_user=current_user)

@task_router.post("/delete/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    current_user: UserModel = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
):
    """Exclui uma tarefa do sistema (dono ou admin)."""
    task_service.delete_task(task_id=task_id, current_user=current_user)
