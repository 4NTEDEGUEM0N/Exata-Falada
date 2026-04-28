from fastapi import APIRouter, Depends, HTTPException, status
from .user_routes import get_current_user
from models.user_model import UserModel
from models.task_model import TaskModel
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from typing import List, Optional
from math import ceil

task_router = APIRouter(prefix="/task", tags=["task"])

class TaskResponse(BaseModel):
    id: int
    pdf_filename: str
    html_filename: Optional[str]
    status: str
    user_id: int

    model_config = ConfigDict(from_attributes=True)

class PaginatedTaskResponse(BaseModel):
    page: int
    total_pages: int
    tasks: List[TaskResponse]


@task_router.get("/", response_model=PaginatedTaskResponse)
async def get_all_tasks(page: int = 1, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED")
    
    limit = 10
    skip = (page - 1) * limit
    
    base_query = db.query(TaskModel).order_by(desc(TaskModel.id))
    total_tasks = base_query.count()
    tasks = base_query.offset(skip).limit(limit).all()

    total_pages = ceil(total_tasks/limit)

    return {"page": page, "total_pages": total_pages, "tasks": tasks}

@task_router.get("/user/{user_id}", response_model=PaginatedTaskResponse)
async def get_all_user_tasks(user_id:int, page: int = 1, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    if user_id != current_user.id and not current_user.admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED")
    
    limit = 10
    skip = (page - 1) * limit
    
    base_query = db.query(TaskModel).filter(TaskModel.user_id == user_id).order_by(desc(TaskModel.id))
    total_tasks = base_query.count()
    tasks = base_query.offset(skip).limit(limit).all()

    total_pages = ceil(total_tasks/limit)

    return {"page": page, "total_pages": total_pages, "tasks": tasks}


@task_router.get("/{task_id}", response_model=TaskResponse)
async def get_task_id(task_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.get(TaskModel, task_id)

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    
    if task.user_id != current_user.id and not current_user.admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED")
    
    return task


@task_router.post("/delete/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.get(TaskModel, task_id)

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    
    if task.user_id != current_user.id and not current_user.admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED")
    
    db.delete(task)
    db.commit()