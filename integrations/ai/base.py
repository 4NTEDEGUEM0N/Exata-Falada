from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Callable

class AIProvider(ABC):
    """Interface abstrata / contrato obrigatório para provedores de Inteligência Artificial."""

    @abstractmethod
    def processar_pagina_imagem(
        self,
        caminho: str,
        pdf_basename: str,
        model_name: str,
        inc_per_page: int,
        log_cb: Callable[[str, int], None]
    ) -> Dict[str, Any]:
        """
        Processa uma imagem de página individual com o modelo de IA,
        retornando um dicionário estruturado com o corpo HTML gerado e metadados.
        """
        pass

    @abstractmethod
    def analisar_imagens_paralelo(
        self,
        pdf_basename: str,
        lista_caminhos: List[str],
        model_name: str,
        workers: int,
        log_cb: Callable[[str, int], None]
    ) -> List[Dict[str, Any]]:
        """
        Processa múltiplas imagens de páginas em paralelo,
        preservando a ordem correta das páginas no documento final.
        """
        pass

    @staticmethod
    @abstractmethod
    def limpar_resposta_html(response_text: str) -> Optional[str]:
        """
        Higieniza a resposta textual da IA, extraindo o bloco HTML puro
        e removendo blocos markdown e formatações indesejadas.
        """
        pass
