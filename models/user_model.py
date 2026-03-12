from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from database import Base


class UserModel(Base):
    __tablename__ = "users"
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    username = Column("nome", String, nullable=False, unique=True)
    password = Column("senha", String, nullable=False)
    admin = Column("admin", Boolean, nullable=False, default=False)

    task = relationship("TaskModel", back_populates="user", cascade="all, delete")
