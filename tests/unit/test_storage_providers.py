import io
import os
import pytest
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError

from app.integrations.storage.base import StorageDeliveryType, MediaType
from app.integrations.storage.local_storage import LocalStorageProvider
from app.integrations.storage.s3_storage import S3StorageProvider
from app.integrations.storage.oci_storage import OCIStorageProvider
from app.integrations.storage.factory import StorageFactory
from app.core import ResourceNotFoundException, DomainException


# ==========================================================
# 1. LocalStorageProvider Tests
# ==========================================================

def test_local_storage_properties(tmp_path):
    upload_dir = str(tmp_path / "uploads")
    output_dir = str(tmp_path / "outputs")
    library_dir = str(tmp_path / "library")

    provider = LocalStorageProvider(upload_dir=upload_dir, output_dir=output_dir, library_dir=library_dir)
    assert provider.is_remote is False
    assert os.path.exists(upload_dir)
    assert os.path.exists(output_dir)
    assert os.path.exists(library_dir)

def test_local_storage_save_upload_file(tmp_path):
    provider = LocalStorageProvider(upload_dir=str(tmp_path / "uploads"), output_dir=str(tmp_path / "outputs"))
    file_obj = io.BytesIO(b"fake pdf content")
    saved_path = provider.save_upload_file(file_obj, "test.pdf")

    assert os.path.exists(saved_path)
    with open(saved_path, "rb") as f:
        assert f.read() == b"fake pdf content"

def test_local_storage_save_output_html(tmp_path):
    provider = LocalStorageProvider(upload_dir=str(tmp_path / "uploads"), output_dir=str(tmp_path / "outputs"))
    data = b"<html><body>Hello</body></html>"
    saved_path = provider.save_output_html(data, "output.html")

    assert os.path.exists(saved_path)
    with open(saved_path, "rb") as f:
        assert f.read() == data

def test_local_storage_get_html_download_info_success(tmp_path):
    output_dir = str(tmp_path / "outputs")
    provider = LocalStorageProvider(upload_dir=str(tmp_path / "uploads"), output_dir=output_dir)
    
    file_path = os.path.join(output_dir, "doc.html")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("content")

    info = provider.get_html_download_info("doc.html")
    assert info.type == StorageDeliveryType.FILE
    assert info.file_path == file_path
    assert info.filename == "doc.html"
    assert info.media_type == MediaType.OCTET_STREAM.value

def test_local_storage_get_html_download_info_not_found(tmp_path):
    provider = LocalStorageProvider(upload_dir=str(tmp_path / "uploads"), output_dir=str(tmp_path / "outputs"))
    with pytest.raises(ResourceNotFoundException):
        provider.get_html_download_info("nonexistent.html")

def test_local_storage_prepare_local_pdf(tmp_path):
    upload_dir = str(tmp_path / "uploads")
    provider = LocalStorageProvider(upload_dir=upload_dir, output_dir=str(tmp_path / "outputs"))

    # Direct existing path
    direct_pdf = tmp_path / "direct.pdf"
    direct_pdf.write_bytes(b"%PDF")
    assert provider.prepare_local_pdf(str(direct_pdf)) == str(direct_pdf)

    # In upload directory
    upload_pdf = tmp_path / "uploads" / "inside_upload.pdf"
    upload_pdf.write_bytes(b"%PDF")
    assert provider.prepare_local_pdf("inside_upload.pdf") == str(upload_pdf)

    # Not found
    with pytest.raises(ResourceNotFoundException):
        provider.prepare_local_pdf("missing.pdf")

def test_local_storage_exists(tmp_path):
    upload_dir = str(tmp_path / "uploads")
    output_dir = str(tmp_path / "outputs")
    provider = LocalStorageProvider(upload_dir=upload_dir, output_dir=output_dir)

    direct = tmp_path / "direct.txt"
    direct.write_text("ok")
    assert provider.exists(str(direct)) is True

    in_upload = tmp_path / "uploads" / "up.txt"
    in_upload.write_text("ok")
    assert provider.exists("up.txt") is True

    in_output = tmp_path / "outputs" / "out.txt"
    in_output.write_text("ok")
    assert provider.exists("out.txt") is True

    assert provider.exists("totally_missing.txt") is False


# ==========================================================
# 2. S3StorageProvider Tests
# ==========================================================

@pytest.fixture
def mock_boto3_s3():
    with patch("boto3.client") as mock_client_factory:
        mock_client = MagicMock()
        mock_client_factory.return_value = mock_client
        yield mock_client

def test_s3_storage_properties(mock_boto3_s3):
    provider = S3StorageProvider(
        bucket_name="my-bucket",
        region="us-east-1",
        access_key="key",
        secret_key="secret"
    )
    assert provider.is_remote is True
    assert provider.bucket_name == "my-bucket"

def test_s3_storage_save_upload_file(mock_boto3_s3):
    provider = S3StorageProvider(bucket_name="my-bucket", region="us-east-1", access_key="k", secret_key="s")
    file_obj = io.BytesIO(b"%PDF")
    key = provider.save_upload_file(file_obj, "book.pdf")

    assert key == "uploads/book.pdf"
    mock_boto3_s3.upload_fileobj.assert_called_once_with(file_obj, "my-bucket", "uploads/book.pdf")

def test_s3_storage_save_output_html(mock_boto3_s3):
    provider = S3StorageProvider(bucket_name="my-bucket", region="us-east-1", access_key="k", secret_key="s")
    data = b"<html></html>"
    key = provider.save_output_html(data, "result.html")

    assert key == "outputs/result.html"
    mock_boto3_s3.put_object.assert_called_once_with(
        Bucket="my-bucket",
        Key="outputs/result.html",
        Body=data,
        ContentType="text/html",
        ContentEncoding="utf-8"
    )

def test_s3_storage_get_html_download_info_success(mock_boto3_s3):
    mock_boto3_s3.generate_presigned_url.return_value = "https://s3.signed.url"
    provider = S3StorageProvider(bucket_name="my-bucket", region="us-east-1", access_key="k", secret_key="s")

    info = provider.get_html_download_info("doc.html")
    assert info.type == StorageDeliveryType.REDIRECT
    assert info.url == "https://s3.signed.url"
    assert info.filename == "doc.html"
    mock_boto3_s3.head_object.assert_called_once_with(Bucket="my-bucket", Key="outputs/doc.html")

def test_s3_storage_get_html_download_info_not_found(mock_boto3_s3):
    error_response = {'Error': {'Code': '404', 'Message': 'Not Found'}}
    mock_boto3_s3.head_object.side_effect = ClientError(error_response, 'HeadObject')
    provider = S3StorageProvider(bucket_name="my-bucket", region="us-east-1", access_key="k", secret_key="s")

    with pytest.raises(ResourceNotFoundException):
        provider.get_html_download_info("doc.html")

def test_s3_storage_get_html_download_info_client_error(mock_boto3_s3):
    error_response = {'Error': {'Code': '500', 'Message': 'Internal'}}
    mock_boto3_s3.head_object.side_effect = ClientError(error_response, 'HeadObject')
    provider = S3StorageProvider(bucket_name="my-bucket", region="us-east-1", access_key="k", secret_key="s")

    with pytest.raises(DomainException):
        provider.get_html_download_info("doc.html")

def test_s3_storage_get_html_download_info_generic_error(mock_boto3_s3):
    mock_boto3_s3.head_object.side_effect = RuntimeError("Network down")
    provider = S3StorageProvider(bucket_name="my-bucket", region="us-east-1", access_key="k", secret_key="s")

    with pytest.raises(DomainException):
        provider.get_html_download_info("doc.html")

def test_s3_storage_prepare_local_pdf(mock_boto3_s3):
    mock_waiter = MagicMock()
    mock_boto3_s3.get_waiter.return_value = mock_waiter
    provider = S3StorageProvider(bucket_name="my-bucket", region="us-east-1", access_key="k", secret_key="s")

    local_path = provider.prepare_local_pdf("uploads/test.pdf")
    assert os.path.exists(local_path)
    os.remove(local_path)

    mock_waiter.wait.assert_called_once_with(Bucket="my-bucket", Key="uploads/test.pdf")

def test_s3_storage_prepare_local_pdf_error(mock_boto3_s3):
    mock_boto3_s3.get_waiter.side_effect = RuntimeError("Waiter failed")
    provider = S3StorageProvider(bucket_name="my-bucket", region="us-east-1", access_key="k", secret_key="s")

    with pytest.raises(ResourceNotFoundException):
        provider.prepare_local_pdf("uploads/test.pdf")

def test_s3_storage_exists(mock_boto3_s3):
    provider = S3StorageProvider(bucket_name="my-bucket", region="us-east-1", access_key="k", secret_key="s")
    
    mock_boto3_s3.head_object.return_value = {}
    assert provider.exists("uploads/test.pdf") is True

    error_response = {'Error': {'Code': '404'}}
    mock_boto3_s3.head_object.side_effect = ClientError(error_response, 'HeadObject')
    assert provider.exists("uploads/test.pdf") is False


# ==========================================================
# 3. OCIStorageProvider Tests
# ==========================================================

def test_oci_storage_properties(mock_boto3_s3):
    provider = OCIStorageProvider(
        bucket_name="oci-bucket",
        region="sa-saopaulo-1",
        namespace="my-namespace",
        access_key="k",
        secret_key="s",
        endpoint_url=None
    )
    assert provider.is_remote is True
    assert provider.endpoint_url == "https://my-namespace.compat.objectstorage.sa-saopaulo-1.oraclecloud.com"

def test_oci_storage_save_upload_file(mock_boto3_s3):
    provider = OCIStorageProvider(bucket_name="oci-bucket", region="sa-saopaulo-1", namespace="ns", access_key="k", secret_key="s", endpoint_url="https://custom.url")
    file_obj = io.BytesIO(b"%PDF")
    key = provider.save_upload_file(file_obj, "book.pdf")

    assert key == "uploads/book.pdf"
    mock_boto3_s3.upload_fileobj.assert_called_once_with(file_obj, "oci-bucket", "uploads/book.pdf")

def test_oci_storage_save_output_html(mock_boto3_s3):
    provider = OCIStorageProvider(bucket_name="oci-bucket", region="sa-saopaulo-1", namespace="ns", access_key="k", secret_key="s", endpoint_url="https://custom.url")
    data = b"<html></html>"
    key = provider.save_output_html(data, "result.html")

    assert key == "outputs/result.html"
    mock_boto3_s3.put_object.assert_called_once_with(
        Bucket="oci-bucket",
        Key="outputs/result.html",
        Body=data,
        ContentType="text/html",
        ContentEncoding="utf-8"
    )

def test_oci_storage_get_html_download_info_success(mock_boto3_s3):
    mock_boto3_s3.generate_presigned_url.return_value = "https://oci.signed.url"
    provider = OCIStorageProvider(bucket_name="oci-bucket", region="sa-saopaulo-1", namespace="ns", access_key="k", secret_key="s", endpoint_url="https://custom.url")

    info = provider.get_html_download_info("doc.html")
    assert info.type == StorageDeliveryType.REDIRECT
    assert info.url == "https://oci.signed.url"
    assert info.filename == "doc.html"

def test_oci_storage_get_html_download_info_not_found(mock_boto3_s3):
    error_response = {'Error': {'Code': 'NoSuchKey'}}
    mock_boto3_s3.head_object.side_effect = ClientError(error_response, 'HeadObject')
    provider = OCIStorageProvider(bucket_name="oci-bucket", region="sa-saopaulo-1", namespace="ns", access_key="k", secret_key="s", endpoint_url="https://custom.url")

    with pytest.raises(ResourceNotFoundException):
        provider.get_html_download_info("doc.html")

def test_oci_storage_get_html_download_info_client_error(mock_boto3_s3):
    error_response = {'Error': {'Code': 'AccessDenied'}}
    mock_boto3_s3.head_object.side_effect = ClientError(error_response, 'HeadObject')
    provider = OCIStorageProvider(bucket_name="oci-bucket", region="sa-saopaulo-1", namespace="ns", access_key="k", secret_key="s", endpoint_url="https://custom.url")

    with pytest.raises(DomainException):
        provider.get_html_download_info("doc.html")

def test_oci_storage_get_html_download_info_generic_error(mock_boto3_s3):
    mock_boto3_s3.head_object.side_effect = RuntimeError("OCI unreachable")
    provider = OCIStorageProvider(bucket_name="oci-bucket", region="sa-saopaulo-1", namespace="ns", access_key="k", secret_key="s", endpoint_url="https://custom.url")

    with pytest.raises(DomainException):
        provider.get_html_download_info("doc.html")

def test_oci_storage_prepare_local_pdf(mock_boto3_s3):
    mock_waiter = MagicMock()
    mock_boto3_s3.get_waiter.return_value = mock_waiter
    provider = OCIStorageProvider(bucket_name="oci-bucket", region="sa-saopaulo-1", namespace="ns", access_key="k", secret_key="s", endpoint_url="https://custom.url")

    local_path = provider.prepare_local_pdf("uploads/oci.pdf")
    assert os.path.exists(local_path)
    os.remove(local_path)

def test_oci_storage_prepare_local_pdf_error(mock_boto3_s3):
    mock_boto3_s3.get_waiter.side_effect = RuntimeError("Download error")
    provider = OCIStorageProvider(bucket_name="oci-bucket", region="sa-saopaulo-1", namespace="ns", access_key="k", secret_key="s", endpoint_url="https://custom.url")

    with pytest.raises(ResourceNotFoundException):
        provider.prepare_local_pdf("uploads/oci.pdf")

def test_oci_storage_exists(mock_boto3_s3):
    provider = OCIStorageProvider(bucket_name="oci-bucket", region="sa-saopaulo-1", namespace="ns", access_key="k", secret_key="s", endpoint_url="https://custom.url")
    
    mock_boto3_s3.head_object.return_value = {}
    assert provider.exists("uploads/oci.pdf") is True

    error_response = {'Error': {'Code': '404'}}
    mock_boto3_s3.head_object.side_effect = ClientError(error_response, 'HeadObject')
    assert provider.exists("uploads/oci.pdf") is False


# ==========================================================
# 4. StorageFactory Tests
# ==========================================================

def test_storage_factory(mock_boto3_s3):
    # Local
    local_p = StorageFactory.get_provider("local")
    assert isinstance(local_p, LocalStorageProvider)

    # AWS
    aws_p = StorageFactory.get_provider("aws")
    assert isinstance(aws_p, S3StorageProvider)

    # Oracle
    oci_p = StorageFactory.get_provider("oracle")
    assert isinstance(oci_p, OCIStorageProvider)

    # Unknown
    with pytest.raises(ValueError) as exc:
        StorageFactory.get_provider("azure")
    assert "Provedor de storage desconhecido: 'azure'" in str(exc.value)
