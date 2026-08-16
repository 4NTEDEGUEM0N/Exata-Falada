import os
import re
import time
import base64
import logging
import concurrent.futures
from functools import partial
from typing import List, Dict, Optional, Any, Callable
from PIL import Image
from google import genai
from config import settings
from prompt_html import get_prompt
from .base import AIProvider
from services.html_service import HtmlService

logger = logging.getLogger(__name__)

class GeminiProvider(AIProvider):
    """Implementação do provedor de IA utilizando o Google Gemini SDK."""

    # Atualizar com frequência a partir de https://ai.google.dev/gemini-api/docs/models
    AVAILABLE_MODELS = [
        "gemini-2.5-flash-lite", 
        "gemini-2.5-flash", 
        "gemini-2.5-pro", 
        "gemini-3.1-flash-lite", 
        "gemini-3-flash-preview", 
        "gemini-3.1-pro-preview", 
        "gemini-3.5-flash"
    ]
    DEFAULT_MODEL = "gemini-2.5-flash-lite"
    RETRY_MODEL = "gemini-3.1-flash-lite"
    MAX_RETRIES = 3

    def __init__(self, api_key: str | None = settings.GOOGLE_API_KEY):
        self.api_key = api_key
        self.client = genai.Client(api_key=self.api_key)

    @property
    def available_models(self) -> List[str]:
        return list(self.AVAILABLE_MODELS)

    @property
    def default_model(self) -> str:
        return self.DEFAULT_MODEL

    @property
    def retry_model(self) -> str:
        return self.RETRY_MODEL

    @property
    def max_retries(self) -> int:
        return self.MAX_RETRIES

    def get_available_models(self) -> List[str]:
        """Método utilitário para retrocompatibilidade."""
        return self.available_models

    def get_default_model(self) -> str:
        """Método utilitário para retrocompatibilidade."""
        return self.default_model

    @staticmethod
    def limpar_resposta_html(response_text: str) -> Optional[str]:
        """Extrai o bloco HTML limpo da resposta do modelo Gemini"""
        return HtmlService.clean_html_response(response_text)

    def processar_pagina_imagem(
        self,
        caminho: str,
        pdf_basename: str,
        model_name: str,
        inc_per_page: int,
        log_cb: Callable[[str, int], None]
    ) -> Dict[str, Any]:
        """
        Processa uma imagem de página individual com o modelo Gemini,
        aplicando tentativas (retries), fallback de modelo e logging de progresso.
        """
        try:
            logger.info(f"Processando: {caminho}...")
            log_cb(f"Processando: {caminho}...", 0)

            if not os.path.exists(caminho):
                raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

            imagem = Image.open(caminho)

            with open(caminho, "rb") as image_file:
                image_data = image_file.read()

            match_pagina = re.search(r"pagina_(\d+)\.png$", caminho)
            current_page_num_in_doc = match_pagina.group(1) if match_pagina else "Desconhecida"

            base64_image_data = base64.b64encode(image_data).decode('utf-8')
            prompt = get_prompt(pdf_basename, imagem.size, current_page_num_in_doc)

            MAX_RETRIES = self.max_retries
            response = None
            html_body = None
            final_finish_reason = 'UNKNOWN'
            current_model = model_name

            for attempt in range(MAX_RETRIES):
                try:
                    response = self.client.models.generate_content(
                        model=current_model,
                        contents=[prompt, imagem]
                    )

                    html_body = None
                    final_finish_reason = 'UNKNOWN'

                    if response and response.candidates:
                        candidate = response.candidates[0]
                        final_finish_reason = candidate.finish_reason.name if candidate.finish_reason else 'UNKNOWN'

                        if final_finish_reason == 'MAX_TOKENS':
                            raise ValueError("MAX_TOKENS")
                        if final_finish_reason == 'RECITATION':
                            raise ValueError("RECITATION")

                        response_text_content = response.text
                        if not response_text_content and candidate.content and candidate.content.parts:
                            response_text_content = ''.join(
                                part.text for part in candidate.content.parts if hasattr(part, 'text') and part.text
                            )

                        html_body = self.limpar_resposta_html(response_text_content or "")

                    if html_body is None:
                        raise ValueError("HTML não pôde ser extraído da resposta do modelo.")

                    # Sucesso na extração
                    break

                except Exception as e:
                    is_max_tokens = "MAX_TOKENS" in str(e).upper()
                    is_recitation = "RECITATION" in str(e).upper()
                    should_switch_model = is_max_tokens or is_recitation

                    if attempt < MAX_RETRIES - 1:
                        if should_switch_model and current_model != self.retry_model:
                            error_type = "MAX_TOKENS" if is_max_tokens else "RECITATION"
                            logger.warning(f"Erro {error_type} na pág {current_page_num_in_doc}. Alternando para o modelo {self.retry_model}.")
                            log_cb(f"⚠️ Erro {error_type} na pág {current_page_num_in_doc} (tentativa {attempt + 1}/{MAX_RETRIES}): {e}. Alternando para modelo {self.retry_model}...", 0)
                            current_model = self.retry_model
                            wait_time = 2
                        else:
                            wait_time = 2 ** attempt * 5
                            logger.warning(f"Erro (tentativa {attempt + 1} de {MAX_RETRIES}) para pág. {current_page_num_in_doc}: {e}. Aguardando {wait_time}s...")
                            log_cb(f"⚠️ Erro na pág {current_page_num_in_doc} (tentativa {attempt + 1}/{MAX_RETRIES}): {e}. Aguardando {wait_time}s...", 0)
                        time.sleep(wait_time)
                    else:
                        if should_switch_model or "HTML não pôde ser extraído" in str(e):
                            logger.warning(f"Erro final (tentativa {attempt + 1} de {MAX_RETRIES}) na pág {current_page_num_in_doc}: {e}.")
                            log_cb(f"⚠️ Erro final na pág {current_page_num_in_doc} (tentativa {attempt + 1}/{MAX_RETRIES}): {e}.", 0)
                            break
                        else:
                            logger.error(f"Erro fatal na pág {current_page_num_in_doc} (tentativa {attempt + 1}/{MAX_RETRIES}): {e}.")
                            log_cb(f"❌ Erro fatal na pág {current_page_num_in_doc} (tentativa {attempt + 1}/{MAX_RETRIES}): {e}.", 0)
                            raise e

            imagem.close()

            if html_body is None:
                logger.warning(f"Aviso: Falha ao extrair HTML para {pdf_basename} (pág {current_page_num_in_doc}).")
                log_cb(f"Aviso: Falha ao extrair HTML para {pdf_basename} (pág {current_page_num_in_doc}).", 0)

            resposta = {
                "page_num_in_doc": current_page_num_in_doc,
                "body": html_body,
                "base64_image": base64_image_data,
                "status": "success" if html_body else "error"
            }
            if html_body is None:
                resposta["error_msg"] = "Falha ao extrair HTML ou erro de MAX_TOKENS."

            if html_body:
                logger.info("✅ Sucesso!")
                log_cb(f"✅ Sucesso na pág {current_page_num_in_doc}!", inc_per_page)
            else:
                log_cb(f"⚠️ Pág {current_page_num_in_doc} processada, mas falhou ao extrair HTML.", inc_per_page)

            time.sleep(2)
            return resposta

        except Exception as e:
            logger.error(f"❌ Erro ao processar {caminho}: {e}", exc_info=True)

            match_pagina = re.search(r"pagina_(\d+)\.png$", caminho)
            current_page_num = match_pagina.group(1) if match_pagina else "Desconhecida"

            error_str = str(e)
            if len(error_str) > 150:
                error_str = error_str[:147] + "..."

            log_cb(f"❌ Erro na pág {current_page_num}: {error_str}", inc_per_page)

            if 'imagem' in locals() and hasattr(imagem, 'close'):
                imagem.close()

            return {
                "page_num_in_doc": current_page_num,
                "body": None,
                "base64_image": None,
                "status": "error",
                "error_msg": str(e)
            }

    def analisar_imagens_paralelo(
        self,
        pdf_basename: str,
        lista_caminhos: List[str],
        model_name: str,
        workers: int,
        log_cb: Callable[[str, int], None]
    ) -> List[Dict[str, Any]]:
        """Executa a conversão de múltiplas imagens em paralelo com ThreadPoolExecutor."""
        total_imgs = len(lista_caminhos)
        inc_per_page = max(1, 65 // total_imgs) if total_imgs > 0 else 0

        logger.info(f"Modelo selecionado: {model_name}")
        log_cb(f"Modelo selecionado: {model_name}", 0)

        func_processar = partial(
            self.processar_pagina_imagem,
            pdf_basename=pdf_basename,
            model_name=model_name,
            inc_per_page=inc_per_page,
            log_cb=log_cb
        )

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            resultados = list(executor.map(func_processar, lista_caminhos))

        return resultados

