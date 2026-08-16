from abc import ABC, abstractmethod
from typing import BinaryIO, Optional
from dataclasses import dataclass
from enum import Enum

class StorageDeliveryType(str, Enum):
    FILE = "file"
    """Retorna o arquivo diretamente do disco local usando FastAPI FileResponse."""

    REDIRECT = "redirect"
    """Retorna um redirecionamento HTTP (307) para uma URL pré-assinada de nuvem (S3/OCI)."""


class MediaType(str, Enum):
    OCTET_STREAM = "application/octet-stream"
    """Fluxo binário genérico. Força o navegador a abrir a caixa de 'Salvar Como / Download'."""

    HTML = "text/html"
    """Documento HTML formatado. Permite renderização visual direta no navegador."""

    PDF = "application/pdf"
    """Documento PDF."""


@dataclass
class StorageDownloadInfo:
    """Estrutura com as informações necessárias para entrega do arquivo via HTTP."""
    type: StorageDeliveryType
    file_path: Optional[str] = None
    url: Optional[str] = None
    filename: Optional[str] = None
    media_type: str = MediaType.OCTET_STREAM.value


class StorageProvider(ABC):
    """Interface abstrata / contrato obrigatório para provedores de armazenamento."""

    @property
    @abstractmethod
    def is_remote(self) -> bool:
        """Indica se o provedor é remoto (nuvem S3/OCI) ou local."""
        pass

    @abstractmethod
    def save_upload_file(self, file_obj: BinaryIO, filename: str) -> str:
        """
        Salva o arquivo PDF de upload no storage.
        Retorna o caminho relativo ou identificador final salvo.
        """
        pass

    @abstractmethod
    def save_output_html(
        self, 
        data: bytes, 
        html_filename: str, 
        content_type: str = MediaType.HTML.value
    ) -> str:
        """
        Salva o arquivo HTML final gerado no storage.
        Retorna o caminho relativo ou identificador final salvo.
        """
        pass

    @abstractmethod
    def get_html_download_info(self, html_filename: str) -> StorageDownloadInfo:
        """
        Retorna as informações necessárias para download do HTML gerado:
        - Para Local: caminho absoluto no disco para FileResponse.
        - Para Nuvem: URL pré-assinada para RedirectResponse.
        """
        pass

    @abstractmethod
    def prepare_local_pdf(self, file_path: str) -> str:
        """
        Garante que o PDF esteja disponível localmente em disco para o PyMuPDF:
        - Para Local: retorna o próprio caminho do arquivo no disco.
        - Para Nuvem: baixa o PDF do bucket para um arquivo temporário local e retorna o caminho.
        """
        pass

    @abstractmethod
    def exists(self, file_path: str) -> bool:
        """Verifica se o arquivo existe no storage."""
        pass
