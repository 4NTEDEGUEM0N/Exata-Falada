import pytest
from unittest.mock import patch, MagicMock, mock_open
from app.integrations.ai.gemini_provider import GeminiProvider
from app.integrations.ai.factory import AIFactory


# ==========================================================
# 1. GeminiProvider Contracts & Properties
# ==========================================================

def test_gemini_provider_models():
    provider = GeminiProvider(api_key="dummy_key")
    assert isinstance(provider.available_models, list)
    assert len(provider.available_models) > 0
    assert all(isinstance(m, str) for m in provider.available_models)
    assert isinstance(provider.default_model, str)
    assert provider.default_model in provider.available_models
    assert isinstance(provider.retry_model, str)
    assert provider.retry_model in provider.available_models
    assert isinstance(provider.max_retries, int)
    assert provider.max_retries > 0


# ==========================================================
# 2. processar_pagina_imagem Scenarios
# ==========================================================

@patch('os.path.exists')
@patch('PIL.Image.open')
@patch('builtins.open', new_callable=mock_open, read_data=b"fake_bytes")
def test_gemini_processar_pagina_imagem_success(mock_file, mock_img_open, mock_exists):
    mock_exists.return_value = True
    mock_img = MagicMock()
    mock_img.size = (200, 300)
    mock_img_open.return_value = mock_img

    provider = GeminiProvider(api_key="dummy_key")
    
    mock_candidate = MagicMock()
    mock_candidate.finish_reason.name = 'STOP'
    mock_response = MagicMock()
    mock_response.candidates = [mock_candidate]
    mock_response.text = "```html\n<p>Página Convertida</p>\n```"

    provider.client.models.generate_content = MagicMock(return_value=mock_response)

    log_messages = []
    def log_cb(msg, inc=0):
        log_messages.append(msg)

    result = provider.processar_pagina_imagem(
        caminho="files/pagina_1.png",
        pdf_basename="documento.pdf",
        model_name="gemini-2.5-flash-lite",
        inc_per_page=10,
        log_cb=log_cb
    )

    assert result["status"] == "success"
    assert result["body"] == "<p>Página Convertida</p>"
    assert result["page_num_in_doc"] == "1"

@patch('os.path.exists')
@patch('PIL.Image.open')
@patch('builtins.open', new_callable=mock_open, read_data=b"fake_bytes")
def test_gemini_processar_pagina_imagem_recitation_fallback(mock_file, mock_img_open, mock_exists):
    mock_exists.return_value = True
    mock_img = MagicMock()
    mock_img.size = (200, 300)
    mock_img_open.return_value = mock_img

    provider = GeminiProvider(api_key="dummy_key")

    mock_recitation = MagicMock()
    mock_recitation_cand = MagicMock()
    mock_recitation_cand.finish_reason.name = 'RECITATION'
    mock_recitation.candidates = [mock_recitation_cand]

    mock_success = MagicMock()
    mock_success_cand = MagicMock()
    mock_success_cand.finish_reason.name = 'STOP'
    mock_success.candidates = [mock_success_cand]
    mock_success.text = "```html\n<p>RecuperadoSP4CcomSP4Csucesso</p>\n```"

    provider.client.models.generate_content = MagicMock(side_effect=[mock_recitation, mock_success])

    log_messages = []
    with patch("time.sleep"):  # Evita delays no teste
        result = provider.processar_pagina_imagem(
            caminho="files/pagina_1.png",
            pdf_basename="documento.pdf",
            model_name="gemini-2.5-flash-lite",
            inc_per_page=10,
            log_cb=lambda msg, inc: log_messages.append(msg)
        )

    assert result["status"] == "success"
    assert result["body"] == "<p>Recuperado com sucesso</p>"
    calls = provider.client.models.generate_content.call_args_list
    assert len(calls) == 2
    assert "SP4C" not in calls[0][1]["contents"][0]
    assert "SP4C" in calls[1][1]["contents"][0]
    assert calls[1][1]["model"] == provider.retry_model

@patch('os.path.exists')
@patch('PIL.Image.open')
@patch('builtins.open', new_callable=mock_open, read_data=b"fake_bytes")
def test_gemini_processar_pagina_imagem_max_tokens_fallback(mock_file, mock_img_open, mock_exists):
    mock_exists.return_value = True
    mock_img = MagicMock()
    mock_img.size = (200, 300)
    mock_img_open.return_value = mock_img

    provider = GeminiProvider(api_key="dummy_key")

    mock_max_tokens = MagicMock()
    mock_cand = MagicMock()
    mock_cand.finish_reason.name = 'MAX_TOKENS'
    mock_max_tokens.candidates = [mock_cand]

    mock_success = MagicMock()
    mock_success_cand = MagicMock()
    mock_success_cand.finish_reason.name = 'STOP'
    mock_success.candidates = [mock_success_cand]
    mock_success.text = "<p>Sucesso Max Tokens</p>"

    provider.client.models.generate_content = MagicMock(side_effect=[mock_max_tokens, mock_success])

    with patch("time.sleep"):
        result = provider.processar_pagina_imagem(
            caminho="files/pagina_2.png",
            pdf_basename="documento.pdf",
            model_name="gemini-2.5-flash-lite",
            inc_per_page=10,
            log_cb=MagicMock()
        )

    assert result["status"] == "success"
    assert result["body"] == "<p>Sucesso Max Tokens</p>"

@patch('os.path.exists')
@patch('PIL.Image.open')
@patch('builtins.open', new_callable=mock_open, read_data=b"fake_bytes")
def test_gemini_processar_pagina_imagem_parts_content(mock_file, mock_img_open, mock_exists):
    mock_exists.return_value = True
    mock_img = MagicMock()
    mock_img.size = (200, 300)
    mock_img_open.return_value = mock_img

    provider = GeminiProvider(api_key="dummy_key")

    mock_response = MagicMock()
    mock_cand = MagicMock()
    mock_cand.finish_reason.name = 'STOP'
    mock_part = MagicMock()
    mock_part.text = "```html\n<p>From Parts</p>\n```"
    mock_cand.content.parts = [mock_part]
    mock_response.candidates = [mock_cand]
    mock_response.text = None  # response.text is empty, fallback to parts

    provider.client.models.generate_content = MagicMock(return_value=mock_response)

    with patch("time.sleep"):
        result = provider.processar_pagina_imagem(
            caminho="files/pagina_3.png",
            pdf_basename="documento.pdf",
            model_name="gemini-2.5-flash-lite",
            inc_per_page=10,
            log_cb=MagicMock()
        )

    assert result["status"] == "success"
    assert result["body"] == "<p>From Parts</p>"

@patch('os.path.exists')
def test_gemini_processar_pagina_imagem_file_not_found(mock_exists):
    mock_exists.return_value = False
    provider = GeminiProvider(api_key="dummy_key")

    result = provider.processar_pagina_imagem(
        caminho="files/pagina_99.png",
        pdf_basename="documento.pdf",
        model_name="gemini-2.5-flash-lite",
        inc_per_page=10,
        log_cb=MagicMock()
    )

    assert result["status"] == "error"
    assert "Arquivo não encontrado" in result["error_msg"]

@patch('os.path.exists')
@patch('PIL.Image.open')
@patch('builtins.open', new_callable=mock_open, read_data=b"fake_bytes")
def test_gemini_processar_pagina_imagem_exhaust_retries(mock_file, mock_img_open, mock_exists):
    mock_exists.return_value = True
    mock_img = MagicMock()
    mock_img.size = (200, 300)
    mock_img_open.return_value = mock_img

    provider = GeminiProvider(api_key="dummy_key")
    # Todas as chamadas falham com erro
    provider.client.models.generate_content = MagicMock(side_effect=RuntimeError("API quota exceeded"))

    with patch("time.sleep"):
        result = provider.processar_pagina_imagem(
            caminho="files/pagina_1.png",
            pdf_basename="documento.pdf",
            model_name="gemini-2.5-flash-lite",
            inc_per_page=10,
            log_cb=MagicMock()
        )

    assert result["status"] == "error"
    assert "API quota exceeded" in result["error_msg"]


# ==========================================================
# 3. analisar_imagens_paralelo Tests
# ==========================================================

def test_gemini_analisar_imagens_paralelo():
    provider = GeminiProvider(api_key="dummy_key")

    mock_result_1 = {"page_num_in_doc": "1", "status": "success", "body": "<p>P1</p>"}
    mock_result_2 = {"page_num_in_doc": "2", "status": "success", "body": "<p>P2</p>"}

    with patch.object(provider, 'processar_pagina_imagem', side_effect=[mock_result_1, mock_result_2]):
        results = provider.analisar_imagens_paralelo(
            pdf_basename="doc.pdf",
            lista_caminhos=["img1.png", "img2.png"],
            model_name="gemini-2.5-flash-lite",
            workers=2,
            log_cb=MagicMock()
        )

    assert len(results) == 2
    assert results[0]["page_num_in_doc"] == "1"
    assert results[1]["page_num_in_doc"] == "2"


# ==========================================================
# 4. AIFactory Tests
# ==========================================================

def test_ai_factory():
    provider = AIFactory.get_provider("gemini")
    assert isinstance(provider, GeminiProvider)

    with pytest.raises(ValueError) as exc:
        AIFactory.get_provider("openai_unknown")
    assert "Provedor de IA desconhecido: 'openai_unknown'" in str(exc.value)
