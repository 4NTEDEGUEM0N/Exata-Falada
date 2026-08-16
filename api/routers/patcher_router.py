import os
from fastapi import APIRouter, Depends, UploadFile, File, Response
from services.patcher_service import PatcherService
from integrations.storage.base import MediaType
from api.deps import get_patcher_service, get_current_user
from models.user_model import UserModel
from core.exceptions import BusinessException
from core.utils import sanitize_filename

patcher_router = APIRouter(prefix="/patcher", tags=["patcher"])

@patcher_router.post("/")
async def patch_html(
    original_file: UploadFile = File(...),
    corrections_file: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_user),
    patcher_service: PatcherService = Depends(get_patcher_service)
):
    """Mescla as correções no documento HTML original e entrega o novo arquivo corrigido."""
    if original_file.content_type != MediaType.HTML.value or corrections_file.content_type != MediaType.HTML.value:
        raise BusinessException("Os arquivos deve ser HTML.")

    original_content = (await original_file.read()).decode('utf-8')
    if "</html>" not in original_content.lower():
        raise BusinessException("Conteúdo HTML inválido no arquivo original.")
    
    corrections_content = (await corrections_file.read()).decode('utf-8')
    if "</html>" not in corrections_content.lower():
        raise BusinessException("Conteúdo HTML inválido no arquivo de correções.")
    
    final_html_content = patcher_service.patch_html_contents(original_content, corrections_content)

    original_pdf_filename = sanitize_filename(original_file.filename or "original.html")
    original_basename = os.path.splitext(original_pdf_filename)[0]
    output_filename = f"{original_basename}_corrigido.html"

    return Response(
        content=final_html_content,
        media_type=MediaType.HTML.value,
        headers={
            "Content-Disposition": f'attachment; filename="{output_filename}"'
        }
    )
