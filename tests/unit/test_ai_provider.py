from unittest.mock import patch, MagicMock, mock_open
from app.integrations.ai.gemini_provider import GeminiProvider

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
    mock_success.text = "```html\n<p>Recuperado</p>\n```"

    provider.client.models.generate_content = MagicMock(side_effect=[mock_recitation, mock_success])

    log_messages = []
    result = provider.processar_pagina_imagem(
        caminho="files/pagina_1.png",
        pdf_basename="documento.pdf",
        model_name="gemini-2.5-flash-lite",
        inc_per_page=10,
        log_cb=lambda msg, inc: log_messages.append(msg)
    )

    assert result["status"] == "success"
    assert result["body"] == "<p>Recuperado</p>"
    calls = provider.client.models.generate_content.call_args_list
    assert len(calls) == 2
    assert calls[1][1]["model"] == provider.retry_model
