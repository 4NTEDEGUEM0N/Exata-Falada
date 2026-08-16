from bs4 import BeautifulSoup
from typing import Dict

class PatcherService:
    """Serviço responsável pela mesclagem e correção de páginas em documentos HTML."""

    @staticmethod
    def extract_pages(soup: BeautifulSoup) -> Dict[str, str]:
        """
        Extrai todas as páginas de um documento HTML parseado.
        Uma página é representada por um elemento <article class='page-content'>,
        opcionalmente precedido por um separador <hr class="page-separator">.
        """
        paginas: Dict[str, str] = {}
        todos_articles = soup.find_all('article', class_='page-content')

        for article in todos_articles:
            page_id = article.get('id')
            if not page_id:
                continue

            separador_anterior = article.find_previous_sibling()
            if (
                separador_anterior 
                and separador_anterior.name == 'hr' 
                and 'page-separator' in (separador_anterior.get('class') or [])
            ):
                html_completo_pagina = str(separador_anterior) + str(article)
            else:
                html_completo_pagina = str(article)

            paginas[page_id] = html_completo_pagina

        return paginas

    def patch_html_contents(self, original_content: str, corrections_content: str) -> str:
        """
        Recebe o conteúdo textual de dois arquivos HTML (original e correções),
        substitui ou adiciona as páginas corrigidas mantendo a ordem numérica,
        e retorna o HTML final formatado (prettify).
        """
        soup_original = BeautifulSoup(original_content, 'html.parser')
        soup_correcoes = BeautifulSoup(corrections_content, 'html.parser')

        paginas_originais = self.extract_pages(soup_original)
        paginas_correcoes = self.extract_pages(soup_correcoes)

        # Atualiza as páginas originais com as correções
        paginas_originais.update(paginas_correcoes)

        # Ordena as páginas pelo identificador numérico final (ex: 'page-1', 'page-2')
        paginas_ordenadas = sorted(
            paginas_originais.items(),
            key=lambda item: int(item[0].split('-')[-1]) if item[0].split('-')[-1].isdigit() else 0
        )

        # Reconstrói a árvore de nós no container principal (<main> ou <body>)
        container_principal = soup_original.find('main') or soup_original.body
        if container_principal:
            container_principal.clear()
            for _, page_html in paginas_ordenadas:
                novas_tags = BeautifulSoup(page_html, 'html.parser')
                container_principal.extend(novas_tags.contents)
        else:
            html_final = "".join([html for _, html in paginas_ordenadas])
            soup_original = BeautifulSoup(f"<html><body>{html_final}</body></html>", 'html.parser')

        return soup_original.prettify()
