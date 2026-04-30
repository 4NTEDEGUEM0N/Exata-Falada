from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy.sql import func


class BookModel(Base):
    __tablename__ = "books"
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    filename = Column("filename", String, nullable=False, unique=True)
    file_path = Column("file_path", String, nullable=False)
    created_at = Column("created_at", DateTime, server_default=func.now(), nullable=False)

    library = relationship("LibraryModel", back_populates="book", cascade="all, delete")