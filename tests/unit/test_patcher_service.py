from bs4 import BeautifulSoup
from app.services.patcher_service import PatcherService

def test_patch_html_contents_updates_and_orders():
    service = PatcherService()
    
    orig_html = """
    <html>
        <head><title>Test</title></head>
        <body>
            <main>
                <article class='page-content' id='page-1'><h2>Página 1 Antiga</h2></article>
                <hr class='page-separator'>
                <article class='page-content' id='page-2'><h2>Página 2 Original</h2></article>
            </main>
        </body>
    </html>
    """

    corrections_html = """
    <html>
        <body>
            <main>
                <article class='page-content' id='page-1'><h2>Página 1 Corrigida</h2></article>
            </main>
        </body>
    </html>
    """

    result = service.patch_html_contents(orig_html, corrections_html)
    assert "Página 1 Corrigida" in result
    assert "Página 2 Original" in result
    assert result.index("Página 1 Corrigida") < result.index("Página 2 Original")

def test_extract_pages_ignores_articles_without_id():
    service = PatcherService()
    html_doc = """
    <html><body>
        <article class='page-content'>No ID</article>
        <article class='page-content' id='page-1'>With ID</article>
    </body></html>
    """
    soup = BeautifulSoup(html_doc, 'html.parser')
    pages = service.extract_pages(soup)
    assert "page-1" in pages
    assert len(pages) == 1

def test_patch_html_contents_fallback_body_container():
    service = PatcherService()
    orig = "<html><body><article class='page-content' id='page-1'>P1</article></body></html>"
    corr = "<html><body><article class='page-content' id='page-1'>P1 New</article></body></html>"
    res = service.patch_html_contents(orig, corr)
    assert "P1 New" in res

def test_patch_html_contents_no_body_or_main():
    service = PatcherService()
    orig = "<article class='page-content' id='page-1'>P1</article>"
    corr = "<article class='page-content' id='page-1'>P1 New</article>"
    res = service.patch_html_contents(orig, corr)
    assert "P1 New" in res
    assert "<body>" in res

