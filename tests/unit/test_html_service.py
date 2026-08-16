from app.services.html_service import HtmlService

def test_clean_html_response_markdown_fence():
    raw = "```html\n<p>Texto com <bdi>x</bdi> e fórmula</p>\n```"
    cleaned = HtmlService.clean_html_response(raw)
    assert cleaned == "<p>Texto com x e fórmula</p>"

def test_clean_html_response_raw_html():
    raw = "<div><span>Conteúdo Puro</span></div>"
    cleaned = HtmlService.clean_html_response(raw)
    assert cleaned == "<div><span>Conteúdo Puro</span></div>"

def test_clean_html_response_empty():
    assert HtmlService.clean_html_response("") is None
    assert HtmlService.clean_html_response("Texto sem tags") is None

def test_build_page_article():
    content = {
        "page_num_in_doc": "1",
        "body": "<p>Página 1 conteúdo</p>",
        "status": "success"
    }
    article = HtmlService.build_page_article(content, is_first_page=True)
    assert "id='page-1'" in article
    assert "Página 1 conteúdo" in article
    assert "hr class=\"page-separator\"" not in article

def test_build_complete_document():
    service = HtmlService()
    pages = [
        {"page_num_in_doc": "1", "body": "<p>P1</p>", "status": "success"},
        {"page_num_in_doc": "2", "body": "<p>P2</p>", "status": "success"}
    ]
    doc = service.build_complete_document("livro_teste.pdf", report_button=False, content_list=pages)
    assert "livro_teste.pdf" in doc
    assert "id='page-1'" in doc
    assert "id='page-2'" in doc
    assert "</html>" in doc
