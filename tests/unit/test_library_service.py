import pytest
from unittest.mock import MagicMock, patch
import io
from app.services.library_service import LibraryService
from app.models.user_model import UserModel
from app.models.book_model import BookModel
from app.core.exceptions import ForbiddenException, BusinessException, ResourceNotFoundException

def test_upload_book_non_admin_forbidden():
    mock_book = MagicMock()
    mock_lib = MagicMock()
    mock_user = MagicMock()
    service = LibraryService(mock_book, mock_lib, mock_user)

    current_user = UserModel(id=2, username="normal", admin=False)
    with pytest.raises(ForbiddenException):
        service.upload_book(io.BytesIO(b"data"), "test.html", "<html></html>", current_user)

def test_upload_book_invalid_html():
    mock_book = MagicMock()
    mock_lib = MagicMock()
    mock_user = MagicMock()
    service = LibraryService(mock_book, mock_lib, mock_user)

    current_user = UserModel(id=1, username="admin", admin=True)
    with pytest.raises(BusinessException):
        service.upload_book(io.BytesIO(b"data"), "test.html", "plain text", current_user)

@patch('shutil.copyfileobj')
@patch('builtins.open')
def test_upload_book_success(mock_open, mock_copy):
    mock_book = MagicMock()
    mock_book.create.side_effect = lambda b: b
    mock_lib = MagicMock()
    mock_user = MagicMock()
    service = LibraryService(mock_book, mock_lib, mock_user)

    current_user = UserModel(id=1, username="admin", admin=True)
    result = service.upload_book(io.BytesIO(b"data"), "meu_livro.html", "<html><body>Ok</body></html>", current_user)
    assert result.filename == "meu_livro.html"

def test_get_book_file_user_without_access():
    mock_book = MagicMock()
    mock_book.get_by_id.return_value = BookModel(id=1, filename="b.html", file_path="path/b.html")
    mock_lib = MagicMock()
    mock_lib.has_user_access.return_value = False
    mock_user = MagicMock()
    service = LibraryService(mock_book, mock_lib, mock_user)

    current_user = UserModel(id=2, username="normal", admin=False)
    with pytest.raises(ForbiddenException):
        service.get_book_file(book_id=1, current_user=current_user)

from datetime import datetime

def test_get_all_books_admin_and_forbidden():
    mock_book = MagicMock()
    now = datetime.now()
    mock_book.get_paginated.return_value = ([BookModel(id=1, filename="b.html", file_path="p", created_at=now)], 1)
    service = LibraryService(mock_book, MagicMock(), MagicMock())

    admin_user = UserModel(id=1, username="admin", admin=True)
    normal_user = UserModel(id=2, username="normal", admin=False)

    res = service.get_all_books(current_user=admin_user)
    assert res.total_pages == 1
    assert len(res.books) == 1

    with pytest.raises(ForbiddenException):
        service.get_all_books(current_user=normal_user)

def test_get_user_books_permission():
    mock_lib = MagicMock()
    mock_lib.get_user_books_paginated.return_value = ([], 0)
    service = LibraryService(MagicMock(), mock_lib, MagicMock())

    admin_user = UserModel(id=1, username="admin", admin=True)
    normal_user = UserModel(id=2, username="normal", admin=False)

    # Own user
    res = service.get_user_books(user_id=2, current_user=normal_user)
    assert res.total_pages == 0

    # Admin accessing other
    res2 = service.get_user_books(user_id=2, current_user=admin_user)
    assert res2.total_pages == 0

    # Normal user accessing other -> forbidden
    with pytest.raises(ForbiddenException):
        service.get_user_books(user_id=1, current_user=normal_user)

def test_get_book_users_permission():
    mock_lib = MagicMock()
    mock_lib.get_book_users_paginated.return_value = ([], 0)
    service = LibraryService(MagicMock(), mock_lib, MagicMock())

    admin_user = UserModel(id=1, username="admin", admin=True)
    normal_user = UserModel(id=2, username="normal", admin=False)

    res = service.get_book_users(book_id=1, current_user=admin_user)
    assert res.total_pages == 0

    with pytest.raises(ForbiddenException):
        service.get_book_users(book_id=1, current_user=normal_user)

def test_add_and_remove_user_access_forbidden():
    service = LibraryService(MagicMock(), MagicMock(), MagicMock())
    normal_user = UserModel(id=2, username="normal", admin=False)

    with pytest.raises(ForbiddenException):
        service.add_user_access(user_id=1, book_id=1, current_user=normal_user)

    with pytest.raises(ForbiddenException):
        service.remove_user_access(user_id=1, book_id=1, current_user=normal_user)
