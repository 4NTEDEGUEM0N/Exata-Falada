import pytest

@pytest.fixture
def auth_headers(client):
    login_response = client.post(
        "/user/token",
        data={"username": "normal_test", "password": "testpass"}
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_patch_html_success(client, auth_headers):
    original_html = """<!DOCTYPE html>
<html>
<head><title>Original</title></head>
<body>
    <main>
        <article class="page-content" id="page-1"><p>Original Page 1</p></article>
        <article class="page-content" id="page-2"><p>Original Page 2</p></article>
    </main>
</body>
</html>"""
    
    corrections_html = """<!DOCTYPE html>
<html>
<head><title>Corrections</title></head>
<body>
    <main>
        <article class="page-content" id="page-2"><p>Corrected Page 2</p></article>
    </main>
</body>
</html>"""

    files = {
        "original_file": ("meu_livro.html", original_html.encode("utf-8"), "text/html"),
        "corrections_file": ("correcoes.html", corrections_html.encode("utf-8"), "text/html")
    }

    response = client.post(
        "/patcher/",
        headers=auth_headers,
        files=files
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert 'attachment; filename="meu_livro_corrigido.html"' in response.headers["content-disposition"]
    
    content = response.text
    assert "Original Page 1" in content
    assert "Corrected Page 2" in content
    assert "Original Page 2" not in content

def test_patch_html_without_auth(client):
    files = {
        "original_file": ("orig.html", b"<html><body></body></html>", "text/html"),
        "corrections_file": ("corr.html", b"<html><body></body></html>", "text/html")
    }
    response = client.post("/patcher/", files=files)
    assert response.status_code == 401

def test_patch_html_invalid_mime_type(client, auth_headers):
    files = {
        "original_file": ("orig.pdf", b"%PDF-1.4", "application/pdf"),
        "corrections_file": ("corr.html", b"<html><body></body></html>", "text/html")
    }
    response = client.post("/patcher/", headers=auth_headers, files=files)
    assert response.status_code == 400
    assert response.json()["detail"] == "Os arquivos deve ser HTML."

def test_patch_html_invalid_original_content(client, auth_headers):
    files = {
        "original_file": ("orig.html", b"plain text without closing html tag", "text/html"),
        "corrections_file": ("corr.html", b"<html><body></body></html>", "text/html")
    }
    response = client.post("/patcher/", headers=auth_headers, files=files)
    assert response.status_code == 400
    assert response.json()["detail"] == "Conteúdo HTML inválido no arquivo original."

def test_patch_html_invalid_corrections_content(client, auth_headers):
    files = {
        "original_file": ("orig.html", b"<html><body></body></html>", "text/html"),
        "corrections_file": ("corr.html", b"broken corrections without closing tag", "text/html")
    }
    response = client.post("/patcher/", headers=auth_headers, files=files)
    assert response.status_code == 400
    assert response.json()["detail"] == "Conteúdo HTML inválido no arquivo de correções."
