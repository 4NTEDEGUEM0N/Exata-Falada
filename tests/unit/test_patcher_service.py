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
