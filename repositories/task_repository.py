from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc
from models.task_model import TaskModel
from .base_repository import BaseRepository
import time

class TaskRepository(BaseRepository[TaskModel]):
    """Repositório responsável pelo acesso aos dados da entidade TaskModel."""
    
    def __init__(self, db: Session):
        super().__init__(TaskModel, db)

    def get_all_paginated(self, page: int = 1, limit: int = 10) -> Tuple[List[TaskModel], int]:
        """Retorna todas as tarefas paginadas por ordem decrescente de ID e o total geral."""
        skip = max(0, (page - 1) * limit)
        base_query = self.db.query(TaskModel).order_by(desc(TaskModel.id))
        total_count = base_query.count()
        tasks = base_query.offset(skip).limit(limit).all()
        return tasks, total_count

    def get_by_user_id_paginated(self, user_id: int, page: int = 1, limit: int = 10) -> Tuple[List[TaskModel], int]:
        """Retorna as tarefas de um usuário específico paginadas por ordem decrescente de ID e o total."""
        skip = max(0, (page - 1) * limit)
        base_query = self.db.query(TaskModel).filter(TaskModel.user_id == user_id).order_by(desc(TaskModel.id))
        total_count = base_query.count()
        tasks = base_query.offset(skip).limit(limit).all()
        return tasks, total_count

    def update_status(self, task_id: int, status: str) -> Optional[TaskModel]:
        """Atualiza o status de uma tarefa e persiste a alteração."""
        task = self.get_by_id(task_id)
        if task:
            task.status = status
            self.db.commit()
            self.db.refresh(task)
        return task

    def append_log_and_progress(self, task_id: int, message: str, increment_progress: int = 0) -> Optional[TaskModel]:
        """Registra uma linha de log com timestamp e opcionalmente incrementa o progresso percentual."""
        task = self.get_by_id(task_id)
        if task:
            timestamp = time.strftime("[%d/%m/%Y %H:%M:%S]")
            new_log = f"{timestamp} {message}\n"
            task.logs = (task.logs or "") + new_log
            if increment_progress > 0:
                task.progress = min(100, (task.progress or 0) + increment_progress)
            self.db.commit()
        return task

    def update_completion(
        self, 
        task_id: int, 
        status: str, 
        html_filename: str, 
        progress: int = 100
    ) -> Optional[TaskModel]:
        """Atualiza a tarefa ao finalizar o processamento com o nome do arquivo HTML gerado."""
        task = self.get_by_id(task_id)
        if task:
            task.status = status
            task.progress = progress
            task.html_filename = html_filename
            self.db.commit()
            self.db.refresh(task)
        return task
