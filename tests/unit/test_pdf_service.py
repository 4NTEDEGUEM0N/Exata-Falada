import pytest
from unittest.mock import patch, MagicMock
from app.services.pdf_service import PdfService

def test_parse_pages_empty_returns_all():
    assert PdfService.parse_pages("", 5) == [0, 1, 2, 3, 4]
    assert PdfService.parse_pages("   ", 3) == [0, 1, 2]

def test_parse_pages_valid_ranges_and_singles():
    pages = PdfService.parse_pages("1-3, 5", 10)
    assert pages == [0, 1, 2, 4]

def test_parse_pages_open_ended_range():
    pages = PdfService.parse_pages("3-", 5)
    assert pages == [2, 3, 4]

def test_parse_pages_empty_commas():
    pages = PdfService.parse_pages("1,,2", 5)
    assert pages == [0, 1]

def test_parse_pages_invalid_string():
    assert PdfService.parse_pages("invalid-range", 10) is None
    assert PdfService.parse_pages("abc", 10) is None
    assert PdfService.parse_pages("1-abc", 10) is None

def test_parse_pages_out_of_bounds():
    assert PdfService.parse_pages("15", 10) is None
    assert PdfService.parse_pages("0", 10) is None
    assert PdfService.parse_pages("1-15", 10) is None

def test_parse_pages_inverted_range():
    assert PdfService.parse_pages("5-2", 10) is None

@patch('fitz.open')
def test_get_page_count(mock_fitz_open):
    mock_doc = MagicMock()
    mock_doc.__len__.return_value = 12
    mock_doc.__enter__.return_value = mock_doc
    mock_fitz_open.return_value = mock_doc

    count = PdfService.get_page_count("dummy.pdf")
    assert count == 12

@patch('fitz.open')
@patch('os.makedirs')
def test_convert_to_images_success(mock_makedirs, mock_fitz_open):
    mock_doc = MagicMock()
    mock_page = MagicMock()
    mock_pixmap = MagicMock()
    mock_page.get_pixmap.return_value = mock_pixmap
    mock_doc.load_page.return_value = mock_page
    mock_doc.__enter__.return_value = mock_doc
    mock_fitz_open.return_value = mock_doc

    logs = []
    pasta, img_paths = PdfService.convert_to_images(
        caminho_pdf="meu_arquivo.pdf",
        paginas_selecionadas=[0, 1],
        dpi=150,
        log_cb=lambda msg, inc: logs.append(msg)
    )

    assert len(img_paths) == 2
    assert mock_pixmap.save.call_count == 2
    assert len(logs) == 2

@patch('shutil.rmtree')
@patch('os.path.exists', return_value=True)
@patch('os.makedirs')
@patch('fitz.open')
def test_convert_to_images_error(mock_fitz_open, mock_makedirs, mock_exists, mock_rmtree):
    mock_fitz_open.side_effect = RuntimeError("Corrupted PDF")

    with pytest.raises(RuntimeError) as exc:
        PdfService.convert_to_images("broken.pdf", [0])
    assert "Erro na conversão PDF para imagem" in str(exc.value)
    mock_rmtree.assert_called_once()

@patch('shutil.rmtree')
@patch('os.path.exists')
def test_cleanup_temp_dir(mock_exists, mock_rmtree):
    mock_exists.return_value = True
    PdfService.cleanup_temp_dir("fake/temp/dir")
    mock_rmtree.assert_called_once_with("fake/temp/dir", ignore_errors=True)

    # Empty dir_path or doesn't exist
    mock_exists.return_value = False
    PdfService.cleanup_temp_dir("")
