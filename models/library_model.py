from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class LibraryModel(Base):
    __tablename__ = "library"
    book_id = Column(Integer, ForeignKey("books.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)

    book = relationship("BookModel", back_populates="library")
    user = relationship("UserModel", back_populates="library")
