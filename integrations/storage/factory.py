from core import settings
from .base import StorageProvider
from .local_storage import LocalStorageProvider
from .s3_storage import S3StorageProvider
from .oci_storage import OCIStorageProvider

class StorageFactory:
    """Factory para instanciar o provedor de armazenamento configurado no ambiente."""

    @staticmethod
    def get_provider(provider: str | None = None) -> StorageProvider:
        selected_provider = provider or settings.STORAGE_PROVIDER
        
        if selected_provider == "local":
            return LocalStorageProvider(
                upload_dir=settings.UPLOAD_DIR,
                output_dir=settings.OUTPUT_DIR,
                library_dir=settings.LIBRARY_DIR
            )
        elif selected_provider == "aws":
            return S3StorageProvider(
                bucket_name=settings.AWS_BUCKET_NAME,
                region=settings.AWS_REGION,
                access_key=settings.AWS_ACCESS_KEY_ID,
                secret_key=settings.AWS_SECRET_ACCESS_KEY
            )
        elif selected_provider == "oracle":
            return OCIStorageProvider(
                bucket_name=settings.OCI_BUCKET_NAME,
                region=settings.OCI_REGION,
                namespace=settings.OCI_NAMESPACE,
                access_key=settings.OCI_ACCESS_KEY_ID,
                secret_key=settings.OCI_SECRET_ACCESS_KEY,
                endpoint_url=settings.OCI_ENDPOINT_URL
            )
        
        raise ValueError(f"Provedor de storage desconhecido: '{selected_provider}'")

