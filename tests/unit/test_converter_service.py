import pytest
import os
from unittest.mock import MagicMock, patch
from app.services.converter_service import ConverterService
from app.models.user_model import UserModel
from app.models.task_model import TaskModel
from app.schemas.task_schemas import TaskStatusEnum
from app.schemas.converter_schemas import ConverterRequest
from app.integrations.storage.base import StorageDownloadInfo, StorageDeliveryType, MediaType
from app.core.exceptions import (
    BusinessException, 
    DomainException,
    ResourceNotFoundException, 
    UnauthorizedException,
    ForbiddenException
)
from app.core import settings


# ==========================================================
# 1. initiate_conversion Tests
# ==========================================================

def test_initiate_conversion_invalid_type():
    service = ConverterService(MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())
    mock_file = MagicMock()
    mock_file.content_type = "text/plain"
    mock_user = UserModel(id=1, username="test", admin=False)

    with pytest.raises(BusinessException) as exc:
        service.initiate_conversion(mock_file, ConverterRequest(), mock_user, MagicMock())
    assert exc.value.status_code == 400

def test_initiate_conversion_file_too_large():
    service = ConverterService(MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())
    mock_file = MagicMock()
    mock_file.content_type = "application/pdf"
    mock_file.size = settings.MAX_FILE_SIZE + 1000
    mock_user = UserModel(id=1, username="test", admin=False)

    with pytest.raises(BusinessException) as exc:
        service.initiate_conversion(mock_file, ConverterRequest(), mock_user, MagicMock())
    assert exc.value.status_code == 413

def test_initiate_conversion_admin_user_custom_params():
    mock_task_repo = MagicMock()
    mock_task_repo.create.return_value = TaskModel(id=10, status=TaskStatusEnum.CREATED.value)
    mock_storage = MagicMock()
    mock_storage.save_upload_file.return_value = "saved_path.pdf"
    mock_ai = MagicMock()
    mock_ai.default_model = "default-gemini"
    
    service = ConverterService(mock_task_repo, mock_storage, mock_ai, MagicMock(), MagicMock())

    mock_file = MagicMock()
    mock_file.content_type = "application/pdf"
    mock_file.size = 1000
    mock_file.filename = "documento.pdf"
    mock_user = UserModel(id=1, username="admin", admin=True)
    req = ConverterRequest(paginas="1-5", dpi=200, workers=8, ai_model="custom-gemini", report_button=True)
    mock_bg = MagicMock()

    result = service.initiate_conversion(mock_file, req, mock_user, mock_bg)
    assert result["task_id"] == 10
    mock_bg.add_task.assert_called_once()
    kwargs = mock_bg.add_task.call_args[1]
    assert kwargs["dpi"] == 200
    assert kwargs["workers"] == 8
    assert kwargs["ai_model"] == "custom-gemini"
    assert kwargs["report_button"] is True

def test_initiate_conversion_normal_user_enforces_defaults():
    mock_task_repo = MagicMock()
    mock_task_repo.create.return_value = TaskModel(id=11, status=TaskStatusEnum.CREATED.value)
    mock_storage = MagicMock()
    mock_ai = MagicMock()
    mock_ai.default_model = "default-gemini"
    
    service = ConverterService(mock_task_repo, mock_storage, mock_ai, MagicMock(), MagicMock())

    mock_file = MagicMock()
    mock_file.content_type = "application/pdf"
    mock_file.size = 1000
    mock_file.filename = "normal.pdf"
    mock_user = UserModel(id=2, username="user", admin=False)
    # Tenta enviar parâmetros avançados mesmo sendo normal user
    req = ConverterRequest(paginas="1-2", dpi=300, workers=16, ai_model="expensive-model", report_button=True)
    mock_bg = MagicMock()

    result = service.initiate_conversion(mock_file, req, mock_user, mock_bg)
    assert result["task_id"] == 11
    kwargs = mock_bg.add_task.call_args[1]
    assert kwargs["dpi"] == settings.DEFAULT_DPI
    assert kwargs["workers"] == settings.DEFAULT_WORKERS
    assert kwargs["ai_model"] == "default-gemini"
    assert kwargs["report_button"] == settings.DEFAULT_REPORT_BUTTON

def test_initiate_conversion_storage_failure():
    mock_task_repo = MagicMock()
    mock_task_repo.create.return_value = TaskModel(id=12, status=TaskStatusEnum.CREATED.value)
    mock_storage = MagicMock()
    mock_storage.save_upload_file.side_effect = RuntimeError("Falha de conexão com S3")
    mock_ai = MagicMock()
    mock_ai.default_model = "default-gemini"

    service = ConverterService(mock_task_repo, mock_storage, mock_ai, MagicMock(), MagicMock())

    mock_file = MagicMock()
    mock_file.content_type = "application/pdf"
    mock_file.size = 1000
    mock_file.filename = "doc.pdf"
    mock_user = UserModel(id=1, username="admin", admin=True)
    mock_bg = MagicMock()

    with pytest.raises(DomainException) as exc_info:
        service.initiate_conversion(mock_file, ConverterRequest(), mock_user, mock_bg)
    
    assert exc_info.value.status_code == 500
    assert "Falha ao armazenar arquivo" in exc_info.value.detail
    mock_task_repo.update_status.assert_called_once_with(12, TaskStatusEnum.ERROR.value)
    mock_task_repo.append_log_and_progress.assert_called_once()
    mock_bg.add_task.assert_not_called()


# ==========================================================
# 2. run_background_pipeline Tests
# ==========================================================

@patch("app.services.converter_service.SessionLocal")
def test_run_background_pipeline_success(mock_session_local):
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db

    mock_task_repo = MagicMock()
    mock_storage = MagicMock()
    mock_storage.prepare_local_pdf.return_value = "/local/path.pdf"

    mock_pdf = MagicMock()
    mock_pdf.get_page_count.return_value = 2
    mock_pdf.parse_pages.return_value = [0, 1]
    mock_pdf.convert_to_images.return_value = ("/tmp/imgs", ["/tmp/imgs/page_1.png", "/tmp/imgs/page_2.png"])

    mock_ai = MagicMock()
    mock_ai.analisar_imagens_paralelo.return_value = [
        {"page_num_in_doc": "1", "status": "success", "body": "<p>P1</p>"},
        {"page_num_in_doc": "2", "status": "success", "body": "<p>P2</p>"}
    ]

    mock_html = MagicMock()
    mock_html.build_complete_document.return_value = "<html><body>Complete</body></html>"

    service = ConverterService(mock_task_repo, mock_storage, mock_ai, mock_pdf, mock_html)

    with patch("app.services.converter_service.TaskRepository", return_value=mock_task_repo):
        service.run_background_pipeline(
            task_id=1,
            caminho_pdf="upload.pdf",
            pdf_basename="documento.pdf",
            paginas_str="1-2",
            dpi=100,
            workers=4,
            ai_model="gemini",
            report_button=False,
            user_id=1
        )

    mock_task_repo.update_completion.assert_called_once_with(
        task_id=1,
        status=TaskStatusEnum.COMPLETED.value,
        html_filename="1_documento.html",
        progress=100
    )
    mock_pdf.cleanup_temp_dir.assert_called_once_with("/tmp/imgs")
    assert mock_db.close.called

@patch("app.services.converter_service.SessionLocal")
def test_run_background_pipeline_with_ai_errors(mock_session_local):
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db

    mock_task_repo = MagicMock()
    mock_storage = MagicMock()
    mock_pdf = MagicMock()
    mock_pdf.get_page_count.return_value = 1
    mock_pdf.parse_pages.return_value = [0]
    mock_pdf.convert_to_images.return_value = ("/tmp/imgs", ["/tmp/imgs/page_1.png"])

    mock_ai = MagicMock()
    mock_ai.analisar_imagens_paralelo.return_value = [
        {"page_num_in_doc": "1", "status": "error", "body": None, "error_msg": "Timeout"}
    ]

    mock_html = MagicMock()
    mock_html.build_complete_document.return_value = "<html><body>Partial</body></html>"

    service = ConverterService(mock_task_repo, mock_storage, mock_ai, mock_pdf, mock_html)

    with patch("app.services.converter_service.TaskRepository", return_value=mock_task_repo):
        service.run_background_pipeline(
            task_id=2,
            caminho_pdf="upload.pdf",
            pdf_basename="documento.pdf",
            paginas_str="",
            dpi=100,
            workers=4,
            ai_model="gemini",
            report_button=False,
            user_id=1
        )

    mock_task_repo.update_completion.assert_called_once_with(
        task_id=2,
        status=TaskStatusEnum.COMPLETED_WITH_ERRORS.value,
        html_filename="2_documento.html",
        progress=100
    )

@patch("app.services.converter_service.SessionLocal")
def test_run_background_pipeline_invalid_pages(mock_session_local):
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db

    mock_task_repo = MagicMock()
    mock_pdf = MagicMock()
    mock_pdf.get_page_count.return_value = 5
    mock_pdf.parse_pages.return_value = None  # Intervalo inválido

    service = ConverterService(mock_task_repo, MagicMock(), MagicMock(), mock_pdf, MagicMock())

    with patch("app.services.converter_service.TaskRepository", return_value=mock_task_repo):
        service.run_background_pipeline(
            task_id=3,
            caminho_pdf="upload.pdf",
            pdf_basename="documento.pdf",
            paginas_str="100-200",
            dpi=100,
            workers=4,
            ai_model="gemini",
            report_button=False,
            user_id=1
        )

    mock_task_repo.update_status.assert_called_with(3, TaskStatusEnum.ERROR.value)


# ==========================================================
# 3. get_task_download_info & get_task_status Tests
# ==========================================================

def test_get_task_download_info_success():
    mock_task_repo = MagicMock()
    task = TaskModel(id=1, user_id=1, status=TaskStatusEnum.COMPLETED.value, html_filename="doc.html")
    mock_task_repo.get_by_id.return_value = task

    mock_storage = MagicMock()
    mock_storage.get_html_download_info.return_value = StorageDownloadInfo(
        type=StorageDeliveryType.FILE,
        file_path="/path/doc.html",
        filename="doc.html"
    )

    service = ConverterService(mock_task_repo, mock_storage, MagicMock(), MagicMock(), MagicMock())
    user = UserModel(id=1, username="test", admin=False)

    info = service.get_task_download_info(task_id=1, current_user=user)
    assert info.filename == "doc.html"
    mock_storage.get_html_download_info.assert_called_once_with("doc.html")

def test_get_task_download_info_not_found():
    mock_task_repo = MagicMock()
    mock_task_repo.get_by_id.return_value = None
    service = ConverterService(mock_task_repo, MagicMock(), MagicMock(), MagicMock(), MagicMock())

    with pytest.raises(ResourceNotFoundException):
        service.get_task_download_info(task_id=999, current_user=UserModel(id=1, username="u", admin=False))

def test_get_task_download_info_unauthorized():
    mock_task_repo = MagicMock()
    task = TaskModel(id=1, user_id=2, status=TaskStatusEnum.COMPLETED.value, html_filename="doc.html")
    mock_task_repo.get_by_id.return_value = task
    service = ConverterService(mock_task_repo, MagicMock(), MagicMock(), MagicMock(), MagicMock())

    with pytest.raises(ForbiddenException):
        service.get_task_download_info(task_id=1, current_user=UserModel(id=3, username="u", admin=False))

def test_get_task_download_info_not_ready():
    mock_task_repo = MagicMock()
    task = TaskModel(id=1, user_id=1, status=TaskStatusEnum.PROCESSING.value)
    mock_task_repo.get_by_id.return_value = task
    service = ConverterService(mock_task_repo, MagicMock(), MagicMock(), MagicMock(), MagicMock())

    with pytest.raises(BusinessException) as exc_info:
        service.get_task_download_info(task_id=1, current_user=UserModel(id=1, username="u", admin=False))
    assert "Arquivo ainda não está pronto" in exc_info.value.detail

def test_get_task_download_info_missing_html_filename():
    mock_task_repo = MagicMock()
    task = TaskModel(id=1, user_id=1, status=TaskStatusEnum.COMPLETED.value, html_filename=None)
    mock_task_repo.get_by_id.return_value = task
    service = ConverterService(mock_task_repo, MagicMock(), MagicMock(), MagicMock(), MagicMock())

    with pytest.raises(ResourceNotFoundException):
        service.get_task_download_info(task_id=1, current_user=UserModel(id=1, username="u", admin=False))

def test_get_task_status_success_owner():
    mock_task_repo = MagicMock()
    task = TaskModel(id=1, user_id=1, status=TaskStatusEnum.PROCESSING.value, progress=50, logs="log...", html_filename=None)
    mock_task_repo.get_by_id.return_value = task
    service = ConverterService(mock_task_repo, MagicMock(), MagicMock(), MagicMock(), MagicMock())

    result = service.get_task_status(task_id=1, current_user=UserModel(id=1, username="u", admin=False))
    assert result["status"] == TaskStatusEnum.PROCESSING.value
    assert result["progress"] == 50
    assert result["logs"] == "log..."

def test_get_task_status_success_admin():
    mock_task_repo = MagicMock()
    task = TaskModel(id=1, user_id=2, status=TaskStatusEnum.COMPLETED.value, progress=100, logs="done", html_filename="f.html")
    mock_task_repo.get_by_id.return_value = task
    service = ConverterService(mock_task_repo, MagicMock(), MagicMock(), MagicMock(), MagicMock())

    result = service.get_task_status(task_id=1, current_user=UserModel(id=99, username="admin", admin=True))
    assert result["status"] == TaskStatusEnum.COMPLETED.value
    assert result["progress"] == 100

def test_get_task_status_not_found():
    mock_task_repo = MagicMock()
    mock_task_repo.get_by_id.return_value = None
    service = ConverterService(mock_task_repo, MagicMock(), MagicMock(), MagicMock(), MagicMock())

    with pytest.raises(ResourceNotFoundException):
        service.get_task_status(task_id=999, current_user=UserModel(id=1, username="u", admin=False))

def test_get_task_status_unauthorized():
    mock_task_repo = MagicMock()
    task = TaskModel(id=1, user_id=2, status=TaskStatusEnum.COMPLETED.value)
    mock_task_repo.get_by_id.return_value = task
    service = ConverterService(mock_task_repo, MagicMock(), MagicMock(), MagicMock(), MagicMock())

    with pytest.raises(ForbiddenException):
        service.get_task_status(task_id=1, current_user=UserModel(id=3, username="u", admin=False))


@patch("app.services.converter_service.SessionLocal")
def test_run_background_pipeline_concurrent_logging(mock_session_local):
    import concurrent.futures
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db

    mock_task_repo = MagicMock()
    mock_storage = MagicMock()
    mock_pdf = MagicMock()
    mock_pdf.get_page_count.return_value = 4
    mock_pdf.parse_pages.return_value = [0, 1, 2, 3]
    mock_pdf.convert_to_images.return_value = ("/tmp/imgs", ["img1.png", "img2.png", "img3.png", "img4.png"])

    def fake_analisar_imagens(pdf_basename, lista_caminhos, model_name, workers, log_cb):
        # Simula chamadas concorrentes a partir de múltiplas threads de workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(log_cb, f"Página {i+1} processada", 25)
                for i in range(len(lista_caminhos))
            ]
            concurrent.futures.wait(futures)
        return [{"page_num_in_doc": str(i+1), "status": "success", "body": "<p>ok</p>"} for i in range(len(lista_caminhos))]

    mock_ai = MagicMock()
    mock_ai.analisar_imagens_paralelo.side_effect = fake_analisar_imagens
    mock_html = MagicMock()
    mock_html.build_complete_document.return_value = "<html><body>ok</body></html>"

    service = ConverterService(mock_task_repo, mock_storage, mock_ai, mock_pdf, mock_html)

    with patch("app.services.converter_service.TaskRepository", return_value=mock_task_repo):
        service.run_background_pipeline(
            task_id=100,
            caminho_pdf="upload.pdf",
            pdf_basename="doc.pdf",
            paginas_str="1-4",
            dpi=100,
            workers=4,
            ai_model="gemini",
            report_button=False,
            user_id=1
        )

    mock_task_repo.update_completion.assert_called_once()
    assert mock_session_local.call_count >= 5
    assert mock_db.close.call_count >= 5


@patch("os.remove")
@patch("os.path.exists", return_value=True)
@patch("app.services.converter_service.SessionLocal")
def test_run_background_pipeline_remote_storage_pdf_cleanup(mock_session_local, mock_exists, mock_remove):
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db

    mock_task_repo = MagicMock()
    mock_storage = MagicMock()
    mock_storage.is_remote = True
    mock_storage.prepare_local_pdf.return_value = "/tmp/downloaded_from_s3.pdf"

    mock_pdf = MagicMock()
    mock_pdf.get_page_count.return_value = 1
    mock_pdf.parse_pages.return_value = [0]
    mock_pdf.convert_to_images.return_value = ("/tmp/imgs", ["img1.png"])

    mock_ai = MagicMock()
    mock_ai.analisar_imagens_paralelo.return_value = [{"page_num_in_doc": "1", "status": "success", "body": "<p>ok</p>"}]
    mock_html = MagicMock()
    mock_html.build_complete_document.return_value = "<html><body>ok</body></html>"

    service = ConverterService(mock_task_repo, mock_storage, mock_ai, mock_pdf, mock_html)

    with patch("app.services.converter_service.TaskRepository", return_value=mock_task_repo):
        service.run_background_pipeline(
            task_id=200,
            caminho_pdf="s3://bucket/remote.pdf",
            pdf_basename="remote.pdf",
            paginas_str="",
            dpi=100,
            workers=4,
            ai_model="gemini",
            report_button=False,
            user_id=1
        )

    mock_remove.assert_called_once_with("/tmp/downloaded_from_s3.pdf")


