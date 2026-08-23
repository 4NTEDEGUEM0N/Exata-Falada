import pytest
from unittest.mock import MagicMock, patch
from app.core.config import Settings
from app.core.database import create_first_admin, upgrade_db, get_db
from app.core.utils import sanitize_filename
from app.models.user_model import UserModel


def test_sanitize_filename():
    assert sanitize_filename("meu arquivo (1).pdf") == "meu_arquivo__1_.pdf"
    assert sanitize_filename("relatorio-final.html") == "relatorio-final.html"
    assert sanitize_filename("teste/../malicioso") == "malicioso"


def test_settings_aws_validation_failure():
    with pytest.raises(ValueError) as exc:
        Settings(
            _env_file=None,
            SECRET_KEY="key",
            GOOGLE_API_KEY="key",
            DATABASE_URL="sqlite:///:memory:",
            ADMIN_USER="admin",
            ADMIN_PASSWORD="pwd",
            STORAGE_PROVIDER="aws",
            AWS_ACCESS_KEY_ID=None
        )
    assert "faltam credenciais da AWS" in str(exc.value)


def test_settings_oracle_validation_failure():
    with pytest.raises(ValueError) as exc:
        Settings(
            _env_file=None,
            SECRET_KEY="key",
            GOOGLE_API_KEY="key",
            DATABASE_URL="sqlite:///:memory:",
            ADMIN_USER="admin",
            ADMIN_PASSWORD="pwd",
            STORAGE_PROVIDER="oracle",
            OCI_ACCESS_KEY_ID=None,
            OCI_SECRET_ACCESS_KEY=None
        )
    assert "faltam credenciais do OCI" in str(exc.value)


def test_settings_oracle_validation_success():
    cfg = Settings(
        SECRET_KEY="key",
        GOOGLE_API_KEY="key",
        DATABASE_URL="sqlite:///:memory:",
        ADMIN_USER="admin",
        ADMIN_PASSWORD="pwd",
        STORAGE_PROVIDER="oracle",
        OCI_ACCESS_KEY_ID="id",
        OCI_SECRET_ACCESS_KEY="sec",
        OCI_BUCKET_NAME="bucket",
        OCI_REGION="sa-saopaulo-1",
        OCI_NAMESPACE="ns"
    )
    assert "https://ns.compat.objectstorage.sa-saopaulo-1.oraclecloud.com" in cfg.OCI_ENDPOINT_URL


@patch("app.core.database.SessionLocal")
def test_create_first_admin_already_exists(mock_session_local):
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db
    mock_db.query.return_value.filter.return_value.first.return_value = UserModel(id=1, username="admin", admin=True)

    create_first_admin()
    mock_db.add.assert_not_called()
    mock_db.close.assert_called_once()


@patch("app.core.database.SessionLocal")
def test_create_first_admin_empty_credentials(mock_session_local):
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with patch("app.core.database.settings") as mock_settings:
        mock_settings.ADMIN_USER = ""
        mock_settings.ADMIN_PASSWORD = ""
        create_first_admin()

    mock_db.add.assert_not_called()
    mock_db.close.assert_called_once()


@patch("app.core.database.SessionLocal")
def test_create_first_admin_exception_rollback(mock_session_local):
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_db.commit.side_effect = RuntimeError("DB locked")

    with patch("app.core.database.settings") as mock_settings:
        mock_settings.ADMIN_USER = "admin"
        mock_settings.ADMIN_PASSWORD = "secret_password"
        create_first_admin()

    mock_db.rollback.assert_called_once()
    mock_db.close.assert_called_once()


@patch("app.core.database._run_upgrade")
def test_upgrade_db(mock_run_upgrade):
    upgrade_db()
    mock_run_upgrade.assert_called_once()


def test_get_db_generator():
    gen = get_db()
    db_session = next(gen)
    assert db_session is not None
    try:
        next(gen)
    except StopIteration:
        pass


def test_domain_exceptions():
    from app.core import (
        DomainException,
        BusinessException,
        ResourceNotFoundException,
        UnauthorizedException,
        ForbiddenException
    )
    d = DomainException("Generic error")
    assert d.status_code == 400
    assert d.detail == "Generic error"

    b = BusinessException("Business rule violated")
    assert b.status_code == 400
    assert b.detail == "Business rule violated"

    r = ResourceNotFoundException()
    assert r.status_code == 404
    assert r.detail == "NOT FOUND"

    u = UnauthorizedException()
    assert u.status_code == 401
    assert u.detail == "UNAUTHORIZED"

    f = ForbiddenException("Access Denied")
    assert f.status_code == 403
    assert f.detail == "Access Denied"
    f_default = ForbiddenException()
    assert f_default.status_code == 403
    assert f_default.detail == "FORBIDDEN"


def test_get_prompt_recitation_toggle():
    from app.core.prompt_html import get_prompt
    prompt_default = get_prompt("teste.pdf", (100, 100), "1", is_recitation=False)
    assert "SP4C" not in prompt_default

    prompt_recitation = get_prompt("teste.pdf", (100, 100), "1", is_recitation=True)
    assert "SP4C" in prompt_recitation
    assert "Text Content" in prompt_recitation
