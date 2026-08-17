import pytest
from app.models.book_model import BookModel
from app.models.library_model import LibraryModel
from unittest.mock import patch
import os

@pytest.fixture
def auth_headers(client):
    login_response = client.post(
        "/user/token",
        data={"username": "normal_test", "password": "testpass"}
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_auth_headers(client):
    login_response = client.post(
        "/user/token",
        data={"username": "admin_test", "password": "testpass"}
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def test_user_id(client, auth_headers):
    me_response = client.get("/user/me", headers=auth_headers)
    return me_response.json()["id"]

@pytest.fixture
def admin_user_id(client, admin_auth_headers):
    me_response = client.get("/user/me", headers=admin_auth_headers)
    return me_response.json()["id"]

@pytest.fixture
def dummy_book(setup_db, tmp_path):
    import uuid
    unique_name = f"dummy_{uuid.uuid4().hex}.html"
    dummy_file = tmp_path / unique_name
    dummy_file.write_text("<html><body>Test Book</body></html>")
    
    book = BookModel(
        filename=unique_name,
        file_path=str(dummy_file)
    )
    setup_db.add(book)
    setup_db.commit()
    setup_db.refresh(book)
    return book

def test_get_all_books_admin(client, admin_auth_headers, dummy_book):
    response = client.get("/library/", headers=admin_auth_headers)
    assert response.status_code == 200
    assert "books" in response.json()

def test_get_all_books_unauthorized(client, auth_headers):
    response = client.get("/library/", headers=auth_headers)
    assert response.status_code == 403

@patch('app.services.library_service.settings')
def test_create_book_success_admin(mock_settings, client, admin_auth_headers, tmp_path):
    mock_settings.LIBRARY_DIR = str(tmp_path)
    file_content = b"<html><body>valid content</body></html>"
    files = {"file": ("test_upload.html", file_content, "text/html")}
    
    response = client.post(
        "/library/",
        headers=admin_auth_headers,
        files=files
    )
    assert response.status_code == 200
    assert response.json()["filename"] == "test_upload.html"

def test_create_book_unauthorized(client, auth_headers):
    file_content = b"<html><body>valid content</body></html>"
    files = {"file": ("test_upload.html", file_content, "text/html")}
    response = client.post("/library/", headers=auth_headers, files=files)
    assert response.status_code == 403

def test_create_book_invalid_type(client, admin_auth_headers):
    file_content = b"<html><body>valid content</body></html>"
    files = {"file": ("test_upload.txt", file_content, "text/plain")}
    response = client.post("/library/", headers=admin_auth_headers, files=files)
    assert response.status_code == 400
    assert response.json()["detail"] == "Os arquivos deve ser HTML."

def test_create_book_invalid_html(client, admin_auth_headers):
    file_content = b"invalid content without html tag"
    files = {"file": ("test_upload.html", file_content, "text/html")}
    response = client.post("/library/", headers=admin_auth_headers, files=files)
    assert response.status_code == 400
    assert response.json()["detail"] == "Conteúdo HTML inválido no arquivo."

def test_add_book_to_user_admin(client, admin_auth_headers, test_user_id, dummy_book, setup_db):
    response = client.post(
        f"/library/add/{test_user_id}/{dummy_book.id}",
        headers=admin_auth_headers
    )
    assert response.status_code == 204
    
    # Verify in DB
    lib_entry = setup_db.query(LibraryModel).filter_by(user_id=test_user_id, book_id=dummy_book.id).first()
    assert lib_entry is not None

def test_add_book_to_user_unauthorized(client, auth_headers, test_user_id, dummy_book):
    response = client.post(
        f"/library/add/{test_user_id}/{dummy_book.id}",
        headers=auth_headers
    )
    assert response.status_code == 403

def test_remove_book_from_user_admin(client, admin_auth_headers, test_user_id, dummy_book, setup_db):
    # Add first
    setup_db.add(LibraryModel(user_id=test_user_id, book_id=dummy_book.id))
    setup_db.commit()
    
    response = client.post(
        f"/library/remove/{test_user_id}/{dummy_book.id}",
        headers=admin_auth_headers
    )
    assert response.status_code == 204
    
    # Verify removal
    lib_entry = setup_db.query(LibraryModel).filter_by(user_id=test_user_id, book_id=dummy_book.id).first()
    assert lib_entry is None

def test_remove_book_not_found(client, admin_auth_headers):
    response = client.post("/library/remove/999/999", headers=admin_auth_headers)
    assert response.status_code == 404

def test_get_all_user_books_self(client, auth_headers, test_user_id, dummy_book, setup_db):
    # Ensure association
    if not setup_db.query(LibraryModel).filter_by(user_id=test_user_id, book_id=dummy_book.id).first():
        setup_db.add(LibraryModel(user_id=test_user_id, book_id=dummy_book.id))
        setup_db.commit()
        
    response = client.get(f"/library/books/{test_user_id}", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()["books"]) > 0

def test_get_all_user_books_admin(client, admin_auth_headers, test_user_id):
    response = client.get(f"/library/books/{test_user_id}", headers=admin_auth_headers)
    assert response.status_code == 200

def test_get_all_user_books_unauthorized(client, auth_headers, admin_user_id):
    response = client.get(f"/library/books/{admin_user_id}", headers=auth_headers)
    assert response.status_code == 403

def test_get_all_book_users_admin(client, admin_auth_headers, dummy_book):
    response = client.get(f"/library/users/{dummy_book.id}", headers=admin_auth_headers)
    assert response.status_code == 200

def test_get_all_book_users_unauthorized(client, auth_headers, dummy_book):
    response = client.get(f"/library/users/{dummy_book.id}", headers=auth_headers)
    assert response.status_code == 403

def test_get_book_file_admin(client, admin_auth_headers, dummy_book):
    response = client.get(f"/library/{dummy_book.id}", headers=admin_auth_headers)
    assert response.status_code == 200
    assert "Test Book" in response.text

def test_get_book_file_user_with_access(client, auth_headers, test_user_id, dummy_book, setup_db):
    if not setup_db.query(LibraryModel).filter_by(user_id=test_user_id, book_id=dummy_book.id).first():
        setup_db.add(LibraryModel(user_id=test_user_id, book_id=dummy_book.id))
        setup_db.commit()
    
    response = client.get(f"/library/{dummy_book.id}", headers=auth_headers)
    assert response.status_code == 200

def test_get_book_file_user_without_access(client, auth_headers, setup_db, tmp_path):
    import uuid
    unique_name2 = f"dummy_{uuid.uuid4().hex}.html"
    dummy_file2 = tmp_path / unique_name2
    dummy_file2.write_text("<html><body>Test Book 2</body></html>")
    book2 = BookModel(filename=unique_name2, file_path=str(dummy_file2))
    setup_db.add(book2)
    setup_db.commit()
    setup_db.refresh(book2)
    
    response = client.get(f"/library/{book2.id}", headers=auth_headers)
    assert response.status_code == 403

def test_get_book_file_not_found(client, admin_auth_headers):
    response = client.get("/library/9999", headers=admin_auth_headers)
    assert response.status_code == 404

def test_delete_book_unauthorized(client, auth_headers, dummy_book):
    response = client.post(f"/library/delete/{dummy_book.id}", headers=auth_headers)
    assert response.status_code == 403

def test_delete_book_not_found(client, admin_auth_headers):
    response = client.post("/library/delete/9999", headers=admin_auth_headers)
    assert response.status_code == 404

def test_delete_book_admin(client, admin_auth_headers, dummy_book):
    response = client.post(f"/library/delete/{dummy_book.id}", headers=admin_auth_headers)
    assert response.status_code == 204
    
    get_response = client.get(f"/library/{dummy_book.id}", headers=admin_auth_headers)
    assert get_response.status_code == 404
