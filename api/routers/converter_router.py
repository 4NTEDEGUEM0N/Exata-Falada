from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, Form
from fastapi.responses import FileResponse, RedirectResponse
from core import settings, BusinessException
from schemas import (
    ConverterRequest, 
    ConverterInitResponse, 
    ModelsResponse,
    TaskStatusResponse
)
from services.converter_service import ConverterService
from integrations.ai.base import AIProvider
from integrations.storage.base import StorageDeliveryType, MediaType
from api.deps import get_converter_service, get_ai_provider, get_current_user
from models.user_model import UserModel

converter_router = APIRouter(prefix="/converter", tags=["converter"])

@converter_router.get("/models", response_model=ModelsResponse)
async def get_models(
    current_user: UserModel = Depends(get_current_user),
    ai_provider: AIProvider = Depends(get_ai_provider)
):
    """Retorna a lista de modelos de IA disponíveis e o modelo padrão do provedor ativo."""
    return ModelsResponse(
        available_models=ai_provider.available_models,
        default_model=ai_provider.default_model
    )

@converter_router.post("/", response_model=ConverterInitResponse)
async def convert_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    paginas: Optional[str] = Form(""),
    dpi: Optional[int] = Form(settings.DEFAULT_DPI),
    workers: Optional[int] = Form(settings.DEFAULT_WORKERS),
    ai_model: Optional[str] = Form(None),
    report_button: Optional[bool] = Form(settings.DEFAULT_REPORT_BUTTON),
    current_user: UserModel = Depends(get_current_user),
    converter_service: ConverterService = Depends(get_converter_service),
    ai_provider: AIProvider = Depends(get_ai_provider)
):
    """Inicia o processo de conversão do arquivo PDF enviado."""
    if file.content_type != MediaType.PDF.value:
        raise BusinessException("O arquivo deve ser um PDF.")

    if file.size and file.size > settings.MAX_FILE_SIZE:
        raise BusinessException("Arquivo muito grande. O limite é 50MB.", status_code=413)

    model_to_use = ai_model or ai_provider.default_model

    converter_req = ConverterRequest(
        paginas=paginas,
        dpi=dpi,
        workers=workers,
        ai_model=model_to_use,
        report_button=report_button
    )

    result = converter_service.initiate_conversion(
        file=file,
        converter_req=converter_req,
        current_user=current_user,
        background_tasks=background_tasks
    )
    return ConverterInitResponse(**result)

@converter_router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def check_task_status(
    task_id: int,
    current_user: UserModel = Depends(get_current_user),
    converter_service: ConverterService = Depends(get_converter_service)
):
    """Consulta o status, progresso e logs de uma tarefa de conversão."""
    data = converter_service.get_task_status(task_id=task_id, current_user=current_user)
    return TaskStatusResponse(**data)

@converter_router.get("/download/{task_id}")
async def download_file(
    task_id: int,
    current_user: UserModel = Depends(get_current_user),
    converter_service: ConverterService = Depends(get_converter_service)
):
    """Obtém o arquivo HTML gerado (via download direto ou redirecionamento para Presigned URL)."""
    info = converter_service.get_task_download_info(task_id=task_id, current_user=current_user)
    if info.type == StorageDeliveryType.REDIRECT:
        return RedirectResponse(url=info.url)
    
    return FileResponse(
        path=info.file_path,
        filename=info.filename,
        media_type=info.media_type,
        content_disposition_type="attachment"
    )
