from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core import Base
from datetime import datetime


class TaskModel(Base):
    __tablename__ = "tasks"
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    pdf_filename = Column("pdf_filename", String, nullable=False)
    html_filename = Column("html_filename", String)
    status = Column("status", String, nullable=False)
    storage_provider = Column("storage_provider", String, nullable=False, default="local")
    created_at = Column("created_at", DateTime, server_default=func.now(), nullable=False)
    
    progress = Column("progress", Integer, default=0)
    logs = Column("logs", Text, default=datetime.now())

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("UserModel", back_populates="task")
