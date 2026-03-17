from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base


class TaskModel(Base):
    __tablename__ = "tasks"
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    pdf_filename = Column("pdf_filename", String, nullable=False)
    html_filename = Column("html_filename", String)
    status = Column("status", String, nullable=False)
    storage_provider = Column("storage_provider", String, nullable=False, default="local")
    
    progress = Column("progress", Integer, default=0)
    logs = Column("logs", Text, default="")

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("UserModel", back_populates="task")
