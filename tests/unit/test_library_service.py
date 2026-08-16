import pytest
from unittest.mock import MagicMock, patch
import io
from app.services.library_service import LibraryService
from app.models.user_model import UserModel
from app.models.book_model import BookModel
from app.core.exceptions import UnauthorizedException, BusinessException, ResourceNotFoundException

def test_upload_book_non_admin_forbidden():
    mock_book = MagicMock()
    mock_lib = MagicMock()
    mock_user = MagicMock()
    service = LibraryService(mock_book, mock_lib, mock_user)

    current_user = UserModel(id=2, username="normal", admin=False)
    with pytest.raises(UnauthorizedException):
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
    with pytest.raises(UnauthorizedException):
        service.get_book_file(book_id=1, current_user=current_user)
