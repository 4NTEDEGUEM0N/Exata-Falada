from fastapi import APIRouter, Depends, HTTPException, status
from .user_routes import get_current_user
from models.user_model import UserModel
from models.task_model import TaskModel
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from database import get_db
from typing import List, Optional

task_router = APIRouter(prefix="/task", tags=["task"])

class TaskResponse(BaseModel):
    id: int
    pdf_filename: str
    html_filename: Optional[str]
    status: str
    user_id: int

    model_config = ConfigDict(from_attributes=True)


@task_router.get("/", response_model=List[TaskResponse])
async def get_all_tasks(skip: int = 0, limit: int = 10, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED")
    
    return db.query(TaskModel).offset(skip).limit(limit).all()

@task_router.get("/me", response_model=List[TaskResponse])
async def get_all_user_tasks(skip: int = 0, limit: int = 10, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(TaskModel).filter(TaskModel.user_id == current_user.id).offset(skip).limit(limit).all()


@task_router.get("/{task_id}", response_model=TaskResponse)
async def get_task_id(task_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.get(TaskModel, task_id)

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    
    if task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED")
    
    return task


@task_router.post("/delete/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.get(TaskModel, task_id)

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    
    if task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED")
    
    db.delete(task)
    db.commit()