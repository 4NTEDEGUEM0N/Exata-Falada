import os
import shutil
from typing import BinaryIO
from config import settings
from core.exceptions import ResourceNotFoundException
from .base import StorageProvider, StorageDownloadInfo, StorageDeliveryType, MediaType

class LocalStorageProvider(StorageProvider):
    """Implementação de armazenamento em sistema de arquivos local."""

    def __init__(
        self,
        upload_dir: str = settings.UPLOAD_DIR,
        output_dir: str = settings.OUTPUT_DIR,
        library_dir: str = settings.LIBRARY_DIR
    ):
        self.upload_dir = upload_dir
        self.output_dir = output_dir
        self.library_dir = library_dir
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.library_dir, exist_ok=True)

    @property
    def is_remote(self) -> bool:
        return False

    def save_upload_file(self, file_obj: BinaryIO, filename: str) -> str:
        """Salva o PDF de upload diretamente no diretório de uploads local."""
        dest_path = os.path.join(self.upload_dir, filename)
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file_obj, buffer)
        return dest_path

    def save_output_html(
        self, 
        data: bytes, 
        html_filename: str, 
        content_type: str = MediaType.HTML.value
    ) -> str:
        """Salva o HTML final gerado diretamente no diretório de saídas local."""
        dest_path = os.path.join(self.output_dir, html_filename)
        with open(dest_path, "wb") as f:
            f.write(data)
        return dest_path

    def get_html_download_info(self, html_filename: str) -> StorageDownloadInfo:
        """Retorna os dados para entrega do arquivo HTML via FileResponse local."""
        file_path = os.path.join(self.output_dir, html_filename)
        if not os.path.exists(file_path):
            raise ResourceNotFoundException("Arquivo não encontrado ou já expirou.")
        return StorageDownloadInfo(
            type=StorageDeliveryType.FILE,
            file_path=file_path,
            filename=html_filename,
            media_type=MediaType.OCTET_STREAM.value
        )

    def prepare_local_pdf(self, file_path: str) -> str:
        """Valida se o PDF está no caminho indicado ou dentro da pasta de uploads."""
        # 1. Se o caminho passado já existe diretamente no disco, usa ele
        if os.path.exists(file_path):
            return file_path
        
        # 2. Se passaram apenas o nome do arquivo, procura na pasta de uploads
        upload_path = os.path.join(self.upload_dir, os.path.basename(file_path))
        if os.path.exists(upload_path):
            return upload_path
            
        raise ResourceNotFoundException(f"Arquivo PDF não encontrado: {file_path}")

    def exists(self, file_path: str) -> bool:
        """Verifica se um arquivo existe no disco."""
        if os.path.isabs(file_path) or os.path.exists(file_path):
            return os.path.exists(file_path)
        in_output = os.path.join(self.output_dir, file_path)
        in_upload = os.path.join(self.upload_dir, file_path)
        return os.path.exists(in_output) or os.path.exists(in_upload)
