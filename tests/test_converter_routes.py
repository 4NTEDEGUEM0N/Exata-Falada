import pytest
from unittest.mock import patch
import os
from models.task_model import TaskModel
from schemas import TaskStatusEnum
from config import settings
from services.converter_service import ConverterService

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

@patch.object(ConverterService, 'run_background_pipeline')
def test_convert_pdf_success(mock_pipeline, client, auth_headers):
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

@patch('api.routers.converter_router.settings')
def test_convert_pdf_huge_file(mock_settings, client, auth_headers):
    mock_settings.MAX_FILE_SIZE = 10  # limite propositalmente pequeno
    
    file_content = b"%PDF-1.4 dummy more than 10 bytes"
    files = {"file": ("test.pdf", file_content, "application/pdf")}
    
    response = client.post(
        "/converter/",
        headers=auth_headers,
        files=files
    )
    
    assert response.status_code == 413
    assert response.json() == {"detail": "Arquivo muito grande. O limite é 50MB."}

def test_download_file_success(client, auth_headers, test_user_id, setup_db):
    # 1. Cria o arquivo HTML na pasta de outputs
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    dummy_path = os.path.join(settings.OUTPUT_DIR, "dummy_output.html")
    with open(dummy_path, "w", encoding="utf-8") as f:
        f.write("<html><body>hello</body></html>")
    
    # 2. Registra a tarefa concluída no banco
    task = TaskModel(
        pdf_filename="test.pdf",
        status=TaskStatusEnum.COMPLETED.value,
        user_id=test_user_id,
        html_filename="dummy_output.html",
        storage_provider="local"
    )
    setup_db.add(task)
    setup_db.commit()

    response = client.get(
        f"/converter/download/{task.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert response.text == "<html><body>hello</body></html>"

def test_download_file_unauthorized_user(client, auth_headers, other_user_auth_headers, setup_db):
    me_response = client.get("/user/me", headers=other_user_auth_headers)
    admin_id = me_response.json()["id"]

    task = TaskModel(
        pdf_filename="test_private.pdf",
        status=TaskStatusEnum.COMPLETED.value,
        user_id=admin_id,
        html_filename="private_output.html",
        storage_provider="local"
    )
    setup_db.add(task)
    setup_db.commit()

    response = client.get(
        f"/converter/download/{task.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 401

def test_download_file_not_found_in_db(client, auth_headers):
    response = client.get(
        "/converter/download/99999",
        headers=auth_headers
    )
    assert response.status_code == 404

def test_download_file_not_found_on_disk(client, auth_headers, test_user_id, setup_db):
    task = TaskModel(
        pdf_filename="test_missing.pdf",
        status=TaskStatusEnum.COMPLETED.value,
        user_id=test_user_id,
        html_filename="missing_on_disk_9999.html",
        storage_provider="local"
    )
    setup_db.add(task)
    setup_db.commit()

    response = client.get(
        f"/converter/download/{task.id}",
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
    assert len(data["available_models"]) > 0

def test_get_status_success(client, auth_headers, test_user_id, setup_db):
    task = TaskModel(
        pdf_filename="test_status.pdf",
        status=TaskStatusEnum.PROCESSING.value,
        user_id=test_user_id,
        storage_provider="local"
    )
    setup_db.add(task)
    setup_db.commit()
    
    response = client.get(
        f"/converter/status/{task.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == TaskStatusEnum.PROCESSING.value
    assert "progress" in data

def test_get_status_unauthorized(client, auth_headers, other_user_auth_headers, setup_db):
    me_response = client.get("/user/me", headers=other_user_auth_headers)
    admin_id = me_response.json()["id"]

    task = TaskModel(
        pdf_filename="test_status_admin.pdf",
        status=TaskStatusEnum.CREATED.value,
        user_id=admin_id,
        storage_provider="local"
    )
    setup_db.add(task)
    setup_db.commit()
    
    response = client.get(
        f"/converter/status/{task.id}",
        headers=auth_headers
    )
    assert response.status_code == 401

def test_get_status_admin_access_other(client, auth_headers, other_user_auth_headers, test_user_id, setup_db):
    task = TaskModel(
        pdf_filename="test_status_normal.pdf",
        status=TaskStatusEnum.CREATED.value,
        user_id=test_user_id,
        storage_provider="local"
    )
    setup_db.add(task)
    setup_db.commit()
    
    response = client.get(
        f"/converter/status/{task.id}",
        headers=other_user_auth_headers
    )
    assert response.status_code == 200

def test_get_status_not_found(client, auth_headers):
    response = client.get(
        "/converter/status/9999",
        headers=auth_headers
    )
    assert response.status_code == 404
