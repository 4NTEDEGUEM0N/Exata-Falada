import boto3
from botocore.exceptions import ClientError
import tempfile
import logging
from typing import BinaryIO
from core import settings, ResourceNotFoundException, DomainException
from .base import StorageProvider, StorageDownloadInfo, StorageDeliveryType, MediaType

logger = logging.getLogger(__name__)

class S3StorageProvider(StorageProvider):
    """Implementação de armazenamento em nuvem AWS S3 utilizando Boto3."""

    def __init__(
        self,
        bucket_name: str | None = settings.AWS_BUCKET_NAME,
        region: str | None = settings.AWS_REGION,
        access_key: str | None = settings.AWS_ACCESS_KEY_ID,
        secret_key: str | None = settings.AWS_SECRET_ACCESS_KEY
    ):
        self.bucket_name = bucket_name
        self.region = region
        self.client = boto3.client(
            's3',
            region_name=self.region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )

    @property
    def is_remote(self) -> bool:
        return True

    def save_upload_file(self, file_obj: BinaryIO, filename: str) -> str:
        """Salva o PDF no bucket sob o prefixo uploads/."""
        key = f"uploads/{filename}"
        self.client.upload_fileobj(file_obj, self.bucket_name, key)
        return key

    def save_output_html(
        self, 
        data: bytes, 
        html_filename: str, 
        content_type: str = MediaType.HTML.value
    ) -> str:
        """Salva o HTML final gerado no bucket sob o prefixo outputs/."""
        key = f"outputs/{html_filename}"
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=data,
            ContentType=content_type,
            ContentEncoding="utf-8"
        )
        return key

    def get_html_download_info(self, html_filename: str) -> StorageDownloadInfo:
        """Gera URL pré-assinada para download do HTML a partir de outputs/."""
        key = f"outputs/{html_filename}"
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=key)
            url = self.client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key,
                    'ResponseContentDisposition': f'attachment; filename="{html_filename}"'
                },
                ExpiresIn=300
            )
            return StorageDownloadInfo(
                type=StorageDeliveryType.REDIRECT,
                url=url,
                filename=html_filename,
                media_type=MediaType.OCTET_STREAM.value
            )
        except ClientError as e:
            if e.response.get('Error', {}).get('Code') in ('404', 'NoSuchKey'):
                raise ResourceNotFoundException("Arquivo não encontrado no storage.")
            logger.error(f"Erro na AWS S3: {e}")
            raise DomainException("Erro no storage provider.", status_code=500)
        except Exception as e:
            logger.error(f"Erro ao consultar AWS S3: {e}")
            raise DomainException("Erro de configuração no AWS Storage.", status_code=500)

    def prepare_local_pdf(self, pdf_key: str) -> str:
        """Baixa o PDF do bucket S3 para um arquivo temporário local e retorna o caminho."""
        try:
            waiter = self.client.get_waiter('object_exists')
            waiter.wait(Bucket=self.bucket_name, Key=pdf_key)
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf_file:
                self.client.download_fileobj(self.bucket_name, pdf_key, tmp_pdf_file)
                return tmp_pdf_file.name
        except Exception as e:
            logger.error(f"Erro ao baixar arquivo da AWS S3 {pdf_key}: {e}")
            raise ResourceNotFoundException(f"Erro ao procurar PDF {pdf_key}: {e}")

    def exists(self, key: str) -> bool:
        """Verifica se uma chave existe no bucket S3."""
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False
