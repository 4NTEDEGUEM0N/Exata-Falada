from app.services.html_service import HtmlService

def test_clean_html_response_markdown_fence():
    raw = "```html\n<p>Texto com <bdi>x</bdi> e <bdi>\\alpha^{2}</bdi> e <bdi> </bdi></p>\n```"
    cleaned = HtmlService.clean_html_response(raw)
    assert cleaned == "<p>Texto com x e \\alpha^{2} e </p>"

def test_clean_html_response_raw_html():
    raw = "<div><span>Conteúdo Puro</span></div>"
    cleaned = HtmlService.clean_html_response(raw)
    assert cleaned == "<div><span>Conteúdo Puro</span></div>"

def test_clean_html_response_empty():
    assert HtmlService.clean_html_response("") is None
    assert HtmlService.clean_html_response("Texto sem tags") is None

def test_build_page_article_first_page():
    content = {
        "page_num_in_doc": "1",
        "body": "<p>Página 1 conteúdo</p>",
        "status": "success"
    }
    article = HtmlService.build_page_article(content, is_first_page=True)
    assert "id='page-1'" in article
    assert "Página 1 conteúdo" in article
    assert "hr class=\"page-separator\"" not in article

def test_build_page_article_subsequent_page_with_image_viewer():
    content = {
        "page_num_in_doc": "2",
        "body": "<p>[Descrição da imagem: Gráfico de funções]</p>",
        "base64_image": "iVBORw0KGgoAAAANSUhEUg==",
        "status": "success"
    }
    article = HtmlService.build_page_article(content, is_first_page=False)
    assert "id='page-2'" in article
    assert '<hr class="page-separator"' in article
    assert '<details class="original-page-viewer">' in article
    assert 'src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUg=="' in article

def test_build_page_article_error_status():
    content = {
        "page_num_in_doc": "3",
        "body": None,
        "status": "error",
        "error_msg": "Timeout no Gemini"
    }
    article = HtmlService.build_page_article(content, is_first_page=False)
    assert "Erro ao processar a página 3: Timeout no Gemini" in article

def test_build_page_article_empty_body_fallback():
    content = {
        "page_num_in_doc": "4",
        "body": None,
        "status": "other"
    }
    article = HtmlService.build_page_article(content, is_first_page=False)
    assert "Conteúdo não pôde ser extraído para a página 4." in article

def test_build_complete_document_with_report_button():
    service = HtmlService()
    pages = [
        {"page_num_in_doc": "1", "body": "<p>P1</p>", "status": "success"}
    ]
    doc = service.build_complete_document("livro_teste.pdf", report_button=True, content_list=pages)
    assert "livro_teste.pdf" in doc
    assert "id='page-1'" in doc
    assert "reportModal" in doc or "relatar" in doc.lower()
    assert "</html>" in doc
