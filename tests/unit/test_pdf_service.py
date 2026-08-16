import pytest
from unittest.mock import patch, MagicMock
from services.pdf_service import PdfService

def test_parse_pages_empty_returns_all():
    pages = PdfService.parse_pages("", 5)
    assert pages == [0, 1, 2, 3, 4]

def test_parse_pages_valid_ranges_and_singles():
    pages = PdfService.parse_pages("1-3, 5", 10)
    assert pages == [0, 1, 2, 4]

def test_parse_pages_invalid_string():
    pages = PdfService.parse_pages("invalid-range", 10)
    assert pages is None

def test_parse_pages_out_of_bounds():
    pages = PdfService.parse_pages("15", 10)
    assert pages is None

def test_parse_pages_inverted_range():
    pages = PdfService.parse_pages("5-2", 10)
    assert pages is None

@patch('fitz.open')
def test_get_page_count(mock_fitz_open):
    mock_doc = MagicMock()
    mock_doc.__len__.return_value = 12
    mock_doc.__enter__.return_value = mock_doc
    mock_fitz_open.return_value = mock_doc

    count = PdfService.get_page_count("dummy.pdf")
    assert count == 12

@patch('shutil.rmtree')
@patch('os.path.exists')
def test_cleanup_temp_dir(mock_exists, mock_rmtree):
    mock_exists.return_value = True
    PdfService.cleanup_temp_dir("fake/temp/dir")
    mock_rmtree.assert_called_once_with("fake/temp/dir", ignore_errors=True)
