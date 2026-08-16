import os
import time
import logging
from typing import Dict, Any, Optional
from fastapi import UploadFile, BackgroundTasks
from config import settings
from repositories.task_repository import TaskRepository
from integrations.storage.base import StorageProvider, StorageDownloadInfo, MediaType
from integrations.ai.base import AIProvider
from services.pdf_service import PdfService
from services.html_service import HtmlService
from models.user_model import UserModel
from models.task_model import TaskModel
from schemas.task_schemas import TaskStatusEnum
from schemas.converter_schemas import ConverterRequest
from core.exceptions import (
    BusinessException, 
    ResourceNotFoundException, 
    UnauthorizedException
)
from core.utils import sanitize_filename
from database import SessionLocal

logger = logging.getLogger(__name__)

class ConverterService:
    """
    Serviço orquestrador do pipeline de conversão de PDFs acessíveis via Inteligência Artificial.
    Coordena Storage, PDF Parsing, IA e montagem do documento HTML.
    """

    def __init__(
        self,
        task_repo: TaskRepository,
        storage_provider: StorageProvider,
        ai_provider: AIProvider,
        pdf_service: PdfService,
        html_service: HtmlService
    ):
        self.task_repo = task_repo
        self.storage_provider = storage_provider
        self.ai_provider = ai_provider
        self.pdf_service = pdf_service
        self.html_service = html_service

    def initiate_conversion(
        self,
        file: UploadFile,
        converter_req: ConverterRequest,
        current_user: UserModel,
        background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """Valida a requisição, persiste o upload, cria o registro da tarefa e agenda o processamento assíncrono."""
        if file.content_type != MediaType.PDF.value:
            raise BusinessException("O arquivo deve ser um PDF.")

        if file.size and file.size > settings.MAX_FILE_SIZE:
            raise BusinessException("Arquivo muito grande. O limite é 50MB.", status_code=413)

        default_model = self.ai_provider.default_model
        # Regra de negócio: usuários não-admin utilizam os parâmetros padrão da aplicação
        if not current_user.admin:
            dpi = settings.DEFAULT_DPI
            workers = settings.DEFAULT_WORKERS
            ai_model = default_model
            report_button = settings.DEFAULT_REPORT_BUTTON
        else:
            dpi = converter_req.dpi or settings.DEFAULT_DPI
            workers = converter_req.workers or settings.DEFAULT_WORKERS
            ai_model = converter_req.ai_model or default_model
            report_button = converter_req.report_button if converter_req.report_button is not None else settings.DEFAULT_REPORT_BUTTON

        sanitized_name = sanitize_filename(file.filename)
        unique_filename = f"{current_user.id}_{int(time.time())}_{sanitized_name}"

        # 1. Salva o PDF no storage ativo (Local, S3 ou OCI)
        saved_path = self.storage_provider.save_upload_file(file.file, unique_filename)

        # 2. Cria o registro da tarefa no banco de dados
        new_task = TaskModel(
            pdf_filename=unique_filename,
            status=TaskStatusEnum.CREATED.value,
            storage_provider=settings.STORAGE_PROVIDER,
            user_id=current_user.id
        )
        task = self.task_repo.create(new_task)

        # 3. Enfileira a tarefa assíncrona
        background_tasks.add_task(
            self.run_background_pipeline,
            task_id=task.id,
            caminho_pdf=saved_path,
            pdf_basename=sanitized_name,
            paginas_str=converter_req.paginas or "",
            dpi=dpi,
            workers=workers,
            ai_model=ai_model,
            report_button=report_button,
            user_id=current_user.id
        )

        return {
            "task_id": task.id,
            "message": "Conversão iniciada com sucesso. Acompanhe o progresso."
        }

    def run_background_pipeline(
        self,
        task_id: int,
        caminho_pdf: str,
        pdf_basename: str,
        paginas_str: str,
        dpi: int,
        workers: int,
        ai_model: str,
        report_button: bool,
        user_id: int
    ) -> None:
        """Pipeline executado em background para processamento de ponta a ponta do PDF."""
        # Cria uma sessão de banco isolada para thread de background
        db = SessionLocal()
        local_task_repo = TaskRepository(db)
        pasta_temp_imgs = None

        def log_cb(message: str, increment_progress: int = 0):
            local_task_repo.append_log_and_progress(task_id, message, increment_progress)

        try:
            local_task_repo.update_status(task_id, TaskStatusEnum.PROCESSING.value)
            log_cb(f"Iniciando processamento do arquivo {pdf_basename}", 5)

            # Passo 1: Garante a disponibilidade do PDF no disco local
            caminho_pdf_local = self.storage_provider.prepare_local_pdf(caminho_pdf)

            # Passo 2: Contagem e seleção de páginas
            total_paginas = self.pdf_service.get_page_count(caminho_pdf_local)
            paginas_selecionadas = self.pdf_service.parse_pages(paginas_str, total_paginas)

            if paginas_selecionadas is None:
                raise ValueError("Intervalo de páginas inválido ou fora dos limites do documento.")

            log_cb(f"Total de páginas no documento: {total_paginas}. Selecionadas: {len(paginas_selecionadas)}", 5)

            # Passo 3: Conversão de páginas para imagens PNG
            pasta_temp_imgs, lista_caminhos_imgs = self.pdf_service.convert_to_images(
                caminho_pdf_local,
                paginas_selecionadas,
                dpi=dpi,
                log_cb=log_cb
            )
            log_cb("Conversão do PDF em imagens concluída com sucesso.", 10)

            # Passo 4: Transcrição das imagens via Provedor de IA
            resultados_ia = self.ai_provider.analisar_imagens_paralelo(
                pdf_basename=pdf_basename,
                lista_caminhos=lista_caminhos_imgs,
                model_name=ai_model,
                workers=workers,
                log_cb=log_cb
            )

            # Passo 5: Montagem do HTML completo e acessível
            html_completo = self.html_service.build_complete_document(
                pdf_filename_title=pdf_basename,
                report_button=report_button,
                content_list=resultados_ia
            )

            # Passo 6: Persistência do HTML de saída no storage
            nome_base_sem_ext = os.path.splitext(pdf_basename)[0]
            html_filename = f"{nome_base_sem_ext}.html"
            html_bytes = html_completo.encode('utf-8')
            self.storage_provider.save_output_html(html_bytes, html_filename)

            # Passo 7: Determina status final e atualiza tarefa
            tem_erros = any(r.get("status") == "error" for r in resultados_ia)
            status_final = (
                TaskStatusEnum.COMPLETED_WITH_ERRORS.value 
                if tem_erros 
                else TaskStatusEnum.COMPLETED.value
            )

            local_task_repo.update_completion(
                task_id=task_id,
                status=status_final,
                html_filename=html_filename,
                progress=100
            )

            if tem_erros:
                log_cb("Finalizado com alguns erros! HTML parcialmente pronto para download.", 0)
            else:
                log_cb("Finalizado com sucesso! HTML pronto para download.", 0)

        except Exception as e:
            logger.error(f"Erro no pipeline da tarefa {task_id}: {e}", exc_info=True)
            local_task_repo.update_status(task_id, TaskStatusEnum.ERROR.value)
            log_cb(f"ERRO CRÍTICO: {e}", 0)

        finally:
            # Passo 8: Limpeza de arquivos temporários
            if pasta_temp_imgs:
                self.pdf_service.cleanup_temp_dir(pasta_temp_imgs)
            db.close()

    def get_task_download_info(self, task_id: int, current_user: UserModel) -> StorageDownloadInfo:
        """Valida autorização e retorna as informações de entrega/download do arquivo HTML gerado."""
        task = self.task_repo.get_by_id(task_id)
        if not task:
            raise ResourceNotFoundException("Tarefa não encontrada")

        if task.user_id != current_user.id and not current_user.admin:
            raise UnauthorizedException()

        if task.status not in (TaskStatusEnum.COMPLETED.value, TaskStatusEnum.COMPLETED_WITH_ERRORS.value):
            raise BusinessException("Arquivo ainda não está pronto para download.")

        if not task.html_filename:
            raise ResourceNotFoundException("Arquivo de saída não registrado.")

        return self.storage_provider.get_html_download_info(task.html_filename)

    def get_task_status(self, task_id: int, current_user: UserModel) -> Dict[str, Any]:
        """Consulta o status, progresso e logs de uma tarefa."""
        task = self.task_repo.get_by_id(task_id)
        if not task:
            raise ResourceNotFoundException("Tarefa não encontrada")

        if task.user_id != current_user.id and not current_user.admin:
            raise UnauthorizedException()

        return {
            "status": task.status,
            "progress": task.progress,
            "logs": task.logs,
            "html_filename": task.html_filename
        }
