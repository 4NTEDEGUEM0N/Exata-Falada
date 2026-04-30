from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from .user_routes import get_current_user, PaginatedUserResponse
from models.user_model import UserModel
from models.book_model import BookModel
from models.library_model import LibraryModel
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from typing import List, Optional
from math import ceil
import re
from config import settings
import os
import shutil
from datetime import datetime

library_router = APIRouter(prefix="/library", tags=["library"])

class BookResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PaginatedBookResponse(BaseModel):
    page: int
    total_pages: int
    books: List[BookResponse]



@library_router.get("/", response_model=PaginatedBookResponse)
async def get_all_books(page: int = 1, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED")
    
    limit = 10
    skip = (page - 1) * limit
    
    base_query = db.query(BookModel).order_by(desc(BookModel.id))
    total_books = base_query.count()
    books = base_query.offset(skip).limit(limit).all()

    total_pages = ceil(total_books/limit)

    return {"page": page, "total_pages": total_pages, "books": books}

@library_router.post("/", response_model=BookResponse)
async def create_book(file: UploadFile = File(...), current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED")
    
    if file.content_type != "text/html":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Os arquivos deve ser HTML.")

    original_content = (await file.read()).decode('utf-8')
    if "</html>" not in original_content.lower():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Conteúdo HTML inválido no arquivo.")
    await file.seek(0)
    
    #if file.size > settings.MAX_FILE_SIZE:
    #    raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail="Arquivo muito grande. O limite é 50MB.")
    
    filename = re.sub(r'[^a-zA-Z0-9.\-_]', '_', file.filename)
    file_path = os.path.join(settings.LIBRARY_DIR, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_book = BookModel(filename=filename, file_path=file_path)
    db.add(new_book)
    db.commit()
    db.refresh(new_book)

    return new_book

@library_router.post("/add/{user_id}/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_book_to_user(user_id: int, book_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED")
    
    new_library = LibraryModel(user_id=user_id, book_id=book_id)
    db.add(new_library)
    db.commit()

@library_router.post("/remove/{user_id}/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_book_from_user(user_id: int, book_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED")
    
    library = db.query(LibraryModel).filter(LibraryModel.user_id == user_id, LibraryModel.book_id == book_id).first()
    if not library:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    
    db.delete(library)
    db.commit()

@library_router.get("/books/{user_id}", response_model=PaginatedBookResponse)
async def get_all_user_books(user_id: int, page: int = 1, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    if user_id != current_user.id and not current_user.admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED")
    
    limit = 10
    skip = (page - 1) * limit
    
    base_query = db.query(BookModel).join(LibraryModel, BookModel.id == LibraryModel.book_id).filter(LibraryModel.user_id == user_id).order_by(desc(BookModel.id))
    total_books = base_query.count()
    books = base_query.offset(skip).limit(limit).all()

    total_pages = ceil(total_books/limit)

    return {"page": page, "total_pages": total_pages, "books": books}

@library_router.get("/users/{book_id}", response_model=PaginatedUserResponse)
async def get_all_book_users(book_id: int, page: int = 1, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED")
    
    limit = 10
    skip = (page - 1) * limit
    
    base_query = db.query(UserModel).join(LibraryModel, UserModel.id == LibraryModel.user_id).filter(LibraryModel.book_id == book_id).order_by(desc(UserModel.id))
    total_users = base_query.count()
    users = base_query.offset(skip).limit(limit).all()

    total_pages = ceil(total_users/limit)

    return {"page": page, "total_pages": total_pages, "users": users}


@library_router.get("/{book_id}")
async def get_book_file(book_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    book = db.get(BookModel, book_id)

    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    
    access = db.query(LibraryModel).filter(LibraryModel.user_id == current_user.id, LibraryModel.book_id == book_id).first()
    
    if access is None and not current_user.admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED")
    
    return FileResponse(
        path=book.file_path, 
        filename=book.filename, 
        media_type="text/html",
        content_disposition_type="inline"
    )


@library_router.post("/delete/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    book = db.get(BookModel, book_id)

    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    
    if not current_user.admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED")
    
    db.delete(book)
    db.commit()