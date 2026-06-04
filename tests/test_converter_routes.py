import pytest
from unittest.mock import patch, mock_open, MagicMock
import os
from models.task_model import TaskModel
from routes.converter_routes import TaskStatusEnum, processar_imagem
from config import settings

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

@patch('routes.converter_routes.settings.STORAGE_PROVIDER', 'local')
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

@patch('routes.converter_routes.settings.STORAGE_PROVIDER', 'local')
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
        html_filename="dummy_output.html",
        storage_provider="local"
    )
    setup_db.add(task)
    setup_db.commit()

    # 3. Use patch for settings.OUTPUT_DIR pointing to tmp_path
    with patch('routes.converter_routes.settings.OUTPUT_DIR', str(tmp_path)), patch('routes.converter_routes.settings.STORAGE_PROVIDER', 'local'):
        response = client.get(
            f"/converter/download/{task.id}",
            headers=auth_headers
        )
    
    assert response.status_code == 200
    assert response.text == "<html><body>hello</body></html>"

def test_download_file_unauthorized_user(client, auth_headers, other_user_auth_headers, setup_db, tmp_path):
    me_response = client.get("/user/me", headers=other_user_auth_headers)
    admin_id = me_response.json()["id"]

    task = TaskModel(
        pdf_filename="test_private.pdf",
        status=TaskStatusEnum.COMPLETED,
        user_id=admin_id,
        html_filename="private_output.html",
        storage_provider="local"
    )
    setup_db.add(task)
    setup_db.commit()

    with patch('routes.converter_routes.settings.OUTPUT_DIR', str(tmp_path)), patch('routes.converter_routes.settings.STORAGE_PROVIDER', 'local'):
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

def test_download_file_not_found_on_disk(client, auth_headers, test_user_id, setup_db, tmp_path):
    task = TaskModel(
        pdf_filename="test_missing.pdf",
        status=TaskStatusEnum.COMPLETED,
        user_id=test_user_id,
        html_filename="missing_on_disk.html",
        storage_provider="local"
    )
    setup_db.add(task)
    setup_db.commit()

    with patch('routes.converter_routes.settings.OUTPUT_DIR', str(tmp_path)), patch('routes.converter_routes.settings.STORAGE_PROVIDER', 'local'):
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


@patch('routes.converter_routes.os.path.exists')
@patch('routes.converter_routes.Image.open')
@patch('builtins.open', new_callable=mock_open, read_data=b"fake_image_bytes")
def test_processar_imagem_recitation_model_switch(mock_file, mock_image_open, mock_exists):
    mock_exists.return_value = True
    
    # Mock PIL Image
    mock_img = MagicMock()
    mock_img.size = (100, 100)
    mock_image_open.return_value = mock_img
    
    # Mock genai.Client
    mock_client = MagicMock()
    
    # We want to simulate a RECITATION error on attempt 1, and success on attempt 2.
    mock_response_recitation = MagicMock()
    mock_candidate_recitation = MagicMock()
    mock_candidate_recitation.finish_reason.name = 'RECITATION'
    mock_response_recitation.candidates = [mock_candidate_recitation]
    
    mock_response_success = MagicMock()
    mock_candidate_success = MagicMock()
    mock_candidate_success.finish_reason.name = 'STOP'
    mock_response_success.candidates = [mock_candidate_success]
    mock_response_success.text = "```html\n<p>Hello World</p>\n```"
    
    mock_client.models.generate_content.side_effect = [
        mock_response_recitation,
        mock_response_success
    ]
    
    log_messages = []
    def log_cb(msg, inc=0):
        log_messages.append(msg)
        
    result = processar_imagem(
        caminho="pagina_1.png",
        pdf_basename="test.pdf",
        client=mock_client,
        gemini_model="gemini-2.0-flash",
        inc_per_page=5,
        log_cb=log_cb
    )
    
    assert result["status"] == "success"
    assert result["body"] == "<p>Hello World</p>"
    
    calls = mock_client.models.generate_content.call_args_list
    assert len(calls) == 2
    assert calls[0][1]["model"] == "gemini-2.0-flash"
    assert calls[1][1]["model"] == settings.RETRY_MODEL
    
    assert any("Erro RECITATION" in msg for msg in log_messages)
    assert any("RECITATION" in msg for msg in log_messages)
    assert any("✅ Sucesso na pág 1!" in msg for msg in log_messages)


@patch('routes.converter_routes.os.path.exists')
@patch('routes.converter_routes.Image.open')
@patch('builtins.open', new_callable=mock_open, read_data=b"fake_image_bytes")
def test_processar_imagem_logs_errors_in_all_attempts(mock_file, mock_image_open, mock_exists):
    mock_exists.return_value = True
    
    mock_img = MagicMock()
    mock_img.size = (100, 100)
    mock_image_open.return_value = mock_img
    
    mock_client = MagicMock()
    
    mock_client.models.generate_content.side_effect = [
        Exception("Api Error 1"),
        Exception("Api Error 2"),
        Exception("Api Error 3")
    ]
    
    log_messages = []
    def log_cb(msg, inc=0):
        log_messages.append(msg)
        
    result = processar_imagem(
        caminho="pagina_1.png",
        pdf_basename="test.pdf",
        client=mock_client,
        gemini_model="gemini-2.0-flash",
        inc_per_page=5,
        log_cb=log_cb
    )
    
    assert result["status"] == "error"
    assert any("Api Error 1" in msg for msg in log_messages)
    assert any("Api Error 2" in msg for msg in log_messages)
    assert any("Api Error 3" in msg for msg in log_messages)
