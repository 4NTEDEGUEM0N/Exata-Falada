import pytest
from unittest.mock import patch, mock_open
import os
from models.task_model import TaskModel
from routes.converter_routes import TaskStatusEnum

@pytest.fixture
def auth_headers(client):
    login_response = client.post(
        "/user/token",
        data={"username": "normal_test", "password": "testpass"}
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def other_user_auth_headers(client):
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

@patch('routes.converter_routes.processar_pdf')
@patch('routes.converter_routes.shutil.copyfileobj')
@patch('builtins.open', new_callable=mock_open)
def test_convert_pdf_success(mock_file, mock_copy, mock_processar, client, auth_headers):
    mock_processar.return_value = "caminho_falso/output.html"
    
    file_content = b"%PDF-1.4 dummy pdf content"
    files = {"file": ("test.pdf", file_content, "application/pdf")}
    
    response = client.post(
        "/converter/",
        headers=auth_headers,
        files=files,
        data={"paginas": "1-2"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert "message" in data
    assert data["message"] == "Conversão iniciada com sucesso. Acompanhe o progresso."

def test_convert_pdf_invalid_type(client, auth_headers):
    file_content = b"just text, not a pdf"
    files = {"file": ("test.txt", file_content, "text/plain")}
    
    response = client.post(
        "/converter/",
        headers=auth_headers,
        files=files,
        data={"paginas": "1"}
    )
    
    assert response.status_code == 400
    assert response.json() == {"detail": "O arquivo deve ser um PDF."}

def test_convert_pdf_without_auth(client):
    file_content = b"%PDF-1.4 dummy pdf content"
    files = {"file": ("test.pdf", file_content, "application/pdf")}
    
    response = client.post(
        "/converter/",
        files=files,
        data={"paginas": "1-2"}
    )
    
    assert response.status_code == 401

@patch('routes.converter_routes.settings')
def test_convert_pdf_huge_file(mock_settings, client, auth_headers):
    mock_settings.MAX_FILE_SIZE = 10  # very small limit
    
    file_content = b"%PDF-1.4 dummy more than 10 bytes"
    files = {"file": ("test.pdf", file_content, "application/pdf")}
    
    response = client.post(
        "/converter/",
        headers=auth_headers,
        files=files
    )
    
    assert response.status_code == 413
    assert response.json() == {"detail": "Arquivo muito grande. O limite é 50MB."}

@patch('routes.converter_routes.processar_pdf')
@patch('routes.converter_routes.shutil.copyfileobj')
@patch('builtins.open', new_callable=mock_open)
def test_convert_pdf_processar_error(mock_file, mock_copy, mock_processar, client, auth_headers):
    # This shouldn't throw an immediate 400 because processar_pdf runs on background now.
    # We should just assert the 200 schedule acceptance.
    mock_processar.side_effect = ValueError("Página inválida")
    
    file_content = b"%PDF-1.4 dummy pdf content"
    files = {"file": ("test.pdf", file_content, "application/pdf")}
    
    response = client.post(
        "/converter/",
        headers=auth_headers,
        files=files,
        data={"paginas": "1-2"}
    )
    
    assert response.status_code == 200
    assert "task_id" in response.json()

def test_download_file_success(client, auth_headers, test_user_id, setup_db, tmp_path):
    # 1. Provide a dummy file in a temp directory
    dummy_html = tmp_path / "dummy_output.html"
    dummy_html.write_text("<html><body>hello</body></html>")
    
    # 2. Add task to DB
    task = TaskModel(
        pdf_filename="test.pdf",
        status=TaskStatusEnum.COMPLETED,
        user_id=test_user_id,
        html_filename="dummy_output.html"
    )
    setup_db.add(task)
    setup_db.commit()

    # 3. Use patch for settings.OUTPUT_DIR pointing to tmp_path
    with patch('routes.converter_routes.settings.OUTPUT_DIR', str(tmp_path)):
        response = client.get(
            "/converter/download/dummy_output.html",
            headers=auth_headers
        )
    
    assert response.status_code == 200
    assert response.text == "<html><body>hello</body></html>"

def test_download_file_unauthorized_user(client, other_user_auth_headers, test_user_id, setup_db, tmp_path):
    task = TaskModel(
        pdf_filename="test_private.pdf",
        status=TaskStatusEnum.COMPLETED,
        user_id=test_user_id,
        html_filename="private_output.html"
    )
    setup_db.add(task)
    setup_db.commit()

    with patch('routes.converter_routes.settings.OUTPUT_DIR', str(tmp_path)):
        response = client.get(
            "/converter/download/private_output.html",
            headers=other_user_auth_headers
        )
    
    assert response.status_code == 401

def test_download_file_not_found_in_db(client, auth_headers):
    response = client.get(
        "/converter/download/nao_existe.html",
        headers=auth_headers
    )
    
    assert response.status_code == 404

def test_download_file_not_found_on_disk(client, auth_headers, test_user_id, setup_db, tmp_path):
    task = TaskModel(
        pdf_filename="test_missing.pdf",
        status=TaskStatusEnum.COMPLETED,
        user_id=test_user_id,
        html_filename="missing_on_disk.html"
    )
    setup_db.add(task)
    setup_db.commit()

    with patch('routes.converter_routes.settings.OUTPUT_DIR', str(tmp_path)):
        response = client.get(
            "/converter/download/missing_on_disk.html",
            headers=auth_headers
        )
    
    assert response.status_code == 404

def test_get_models(client, auth_headers):
    response = client.get(
        "/converter/models",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "available_models" in data
    assert "default_model" in data
    assert isinstance(data["available_models"], list)
    assert isinstance(data["default_model"], str)
