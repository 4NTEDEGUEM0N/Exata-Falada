import re
import html
from typing import List, Dict, Any, Optional
from app.core.prompt_html import get_html

class HtmlService:
    """
    Serviço especializado em processamento, higienização e construção
    de documentos HTML acessíveis para o leitor de tela.
    """

    @staticmethod
    def clean_html_response(response_text: str) -> Optional[str]:
        """
        Extrai o bloco HTML da resposta do modelo de IA,
        removendo blocos markdown e higienizando tags <bdi>.
        """
        if not response_text:
            return None

        html_body = None
        match = re.search(r"```html\s*(.*?)\s*```", response_text, re.DOTALL | re.IGNORECASE)
        if match:
            html_body = match.group(1).strip()
        else:
            trimmed_text = response_text.strip()
            if (
                trimmed_text.startswith("<") 
                and trimmed_text.endswith(">") 
                and re.search(r"<p|<div|<span|<table|<ul|<ol|<h[1-6]", trimmed_text, re.IGNORECASE)
            ):
                html_body = trimmed_text

        if html_body:
            html_body = re.sub(r'<bdi>([a-zA-Z0-9_](?:<sup>.*?</sup>)?)</bdi>', r'\1', html_body)
            html_body = re.sub(r'<bdi>(\\[a-zA-Z]+(?:\{.*?\})?(?:\s*\^\{.*?\})?(?:\s*_\{.*?\})?)</bdi>', r'\1', html_body)
            html_body = re.sub(r'<bdi>\s*</bdi>', '', html_body)

        return html_body

    @staticmethod
    def build_page_article(content_data: Dict[str, Any], is_first_page: bool = False) -> str:
        """
        Constrói o bloco semântico <article class='page-content'> para uma página específica,
        incluindo o visualizador de imagem original em base64 se houver descrições de imagem.
        """
        page_num_in_doc = content_data.get("page_num_in_doc", "Desconhecida")
        html_body = content_data.get("body")
        base64_image = content_data.get("base64_image")
        status = content_data.get("status", "success")
        error_msg = content_data.get("error_msg", "")

        parts = []
        if not is_first_page:
            parts.append('<hr class="page-separator" aria-hidden="true">\n')

        parts.append(
            f"<article class='page-content' id='page-{page_num_in_doc}' "
            f"aria-labelledby='page-heading-{page_num_in_doc}'>\n"
        )
        parts.append(f"<h2 id='page-heading-{page_num_in_doc}'>Página {page_num_in_doc}</h2>\n")

        if html_body:
            parts.append(html_body)
        elif status == "error":
            parts.append(f"<p><i>[Erro ao processar a página {page_num_in_doc}: {html.escape(error_msg)}]</i></p>")
        else:
            parts.append(f"<p><i>[Conteúdo não pôde ser extraído para a página {page_num_in_doc}.]</i></p>")

        if html_body and base64_image and "[Descrição da imagem:" in html_body:
            safe_alt_text = html.escape(f"Imagem original da página {page_num_in_doc}")
            parts.append(f"""
                <details class="original-page-viewer">
                    <summary>Ver Imagem da Página Original {page_num_in_doc}</summary>
                    <div style="text-align: center; padding: 10px;">
                        <img src="data:image/png;base64,{base64_image}" alt="{safe_alt_text}" style="max-width: 100%; height: auto;" aria-hidden="true">
                    </div>
                </details>
            """)

        parts.append("\n</article>\n")
        return "".join(parts)

    def build_complete_document(
        self,
        pdf_filename_title: str,
        report_button: bool,
        content_list: List[Dict[str, Any]]
    ) -> str:
        """
        Monta o documento HTML final completo combinando o template de acessibilidade,
        todos os artigos de páginas gerados e o formulário de relato se ativado.
        """
        header_html, report_button_forms = get_html(pdf_filename_title, report_button)
        
        pages_html = []
        for i, content_data in enumerate(content_list):
            page_chunk = self.build_page_article(content_data, is_first_page=(i == 0))
            pages_html.append(page_chunk)

        body_content = "".join(pages_html)
        full_html = f"{header_html}\n{body_content}\n    </main> \n    {report_button_forms}\n</body>\n</html>"
        return full_html
