import os
import time
import shutil
import logging
from typing import List, Optional, Tuple, Callable
import fitz

logger = logging.getLogger(__name__)

class PdfService:
    """Serviço responsável pela manipulação, contagem, parsing e conversão de PDFs via PyMuPDF."""

    @staticmethod
    def parse_pages(string_paginas: str, total_paginas: int) -> Optional[List[int]]:
        """
        Interpreta uma string de seleção de páginas (ex: '1-3, 5, 8-10') e retorna
        a lista de índices 0-indexed ordenados e sem duplicatas.
        Retorna None se a string contiver formatação inválida ou índices fora dos limites.
        """
        if not string_paginas or not string_paginas.strip():
            return list(range(total_paginas))

        paginas = set()
        partes = string_paginas.strip().replace(" ", "").split(',')
        for parte in partes:
            parte = parte.strip()
            if not parte:
                continue
            if '-' in parte:
                inicio, fim = parte.split('-', 1)
                try:
                    start_idx = int(inicio) - 1
                    end_idx = (int(fim) - 1) if fim else (total_paginas - 1)
                    if not (0 <= start_idx < total_paginas and 0 <= end_idx < total_paginas and start_idx <= end_idx):
                        return None
                    paginas.update(range(start_idx, end_idx + 1))
                except ValueError:
                    return None
            else:
                try:
                    idx = int(parte) - 1
                    if not (0 <= idx < total_paginas):
                        return None
                    paginas.add(idx)
                except ValueError:
                    return None

        return sorted(list(paginas))

    @staticmethod
    def get_page_count(caminho_pdf: str) -> int:
        """Abre o documento PDF e retorna a quantidade total de páginas."""
        with fitz.open(caminho_pdf) as doc:
            return len(doc)

    @staticmethod
    def convert_to_images(
        caminho_pdf: str,
        paginas_selecionadas: List[int],
        dpi: int = 100,
        log_cb: Callable[[str, int], None] = lambda msg, inc: None
    ) -> Tuple[str, List[str]]:
        """
        Converte as páginas selecionadas do PDF em imagens PNG em uma pasta temporária.
        Retorna a tupla (pasta_temporaria, lista_de_caminhos_das_imagens).
        """
        pdf_basename = os.path.basename(caminho_pdf)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        pasta_saida = os.path.join('files/temp_processing', f"{pdf_basename}_{timestamp}")
        image_paths = []

        try:
            os.makedirs(pasta_saida, exist_ok=True)
            with fitz.open(caminho_pdf) as documento:
                for numero_pagina in paginas_selecionadas:
                    pagina = documento.load_page(numero_pagina)
                    imagem = pagina.get_pixmap(dpi=dpi)

                    nome_arquivo = os.path.join(pasta_saida, f"pagina_{numero_pagina + 1}.png")
                    imagem.save(nome_arquivo)

                    image_paths.append(nome_arquivo)
                    logger.info(f"Página {numero_pagina + 1} salva como {nome_arquivo}")
                    log_cb(f"Página {numero_pagina + 1} extraída.", 0)
        except Exception as e:
            logger.error(f"Erro ao converter PDF para imagens: {e}", exc_info=True)
            if os.path.exists(pasta_saida):
                shutil.rmtree(pasta_saida, ignore_errors=True)
            raise RuntimeError(f"Erro na conversão PDF para imagem: {e}")

        return pasta_saida, image_paths

    @staticmethod
    def cleanup_temp_dir(dir_path: str) -> None:
        """Remove a pasta temporária de processamento de imagens."""
        if dir_path and os.path.exists(dir_path):
            shutil.rmtree(dir_path, ignore_errors=True)
