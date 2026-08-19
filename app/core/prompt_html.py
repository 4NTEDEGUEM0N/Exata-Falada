import html

def get_prompt(page_filename: str, img_dimensions: tuple, current_page_num_in_doc: str):
    prompt = f"""
Analyze the content of the provided image (filename: {page_filename}, dimensions: {img_dimensions[0]}x{img_dimensions[1]} pixels, representing page {current_page_num_in_doc} of the document). Your goal is to convert this page into an accessible HTML format suitable for screen readers, specifically targeting visually impaired STEM students reading Portuguese content. Don't change the original text or language, even if it's wrong; the main goal is fidelity to the original text.
**Instructions:**
1.  **Text Content (MAXIMUM FIDELITY REQUIRED):**
    * Extract ALL readable text from the image **EXACTLY** as it appears.
    * Preserve the original language (Portuguese) and the **PRECISE WORDING AND ORDER OF WORDS**.
    * Do NOT paraphrase, reorder, or 'correct' the text. Reproduce it verbatim.
    * Preserve paragraph structure where possible.
    * **Omit standalone page numbers** that typically appear at the very top or bottom of a page, unless they are part of a sentence or reference.
    * **CRITICAL: If the page is blank or contains only minimal, non-textual content such as small, non-descriptive shapes or lines, output only the text "<p>Página em branco</p>" (without quotes).

2.  **Web Links (URLs):**
    * Identify all web addresses (URLs, links) in the text (e.g., starting with `http://`, `https://`, `www.`).
    * **CRITICAL: You MUST format them as clickable HTML links using the `<a>` tag.**
    * The `href` attribute must contain the full, correct URL, and the link text should also be the full URL.
    * **Example:** If the text reads `disponível em https://www.exemplo.com/doc.pdf`, the HTML output MUST be `disponível em <a href="https://www.exemplo.com/doc.pdf">https://www.exemplo.com/doc.pdf</a>`.

3.  **Mathematical Equations:**
    * Identify ALL mathematical equations, formulas, and expressions.
    * Convert them accurately into LaTeX format.
    * **The LaTeX-rendered equation itself MUST be placed inside an element that is VISIBLE on screen but HIDDEN from screen readers. Do this by wrapping the equation with an element containing `aria-hidden="true"`. <span aria-hidden="true">\\(t > 0\\)</span>. Use this for both inline mathematics and display mathematics (equations on their own line).
    * **Immediately AFTER each such equation, insert another element that is INVISIBLE visually but READ by screen readers. Use a `.sr-only` class for this. The content of this element must be a NATURAL LANGUAGE description in **Brazilian Portuguese**, describing how the equation should be read aloud. <span class="sr-only">t maior que 0</span>. Use this for both inline mathematics and display mathematics (equations on their own line).

    ---
    **[START OF EQUATION READING GUIDELINES]**
    To ensure this description is clear and unambiguous, you MUST follow these essential guidelines:

    **Objective:** Produce a verbal description of mathematical expressions that is precise, explicit, and easy to understand for someone who cannot see the equation. Clarity has priority over brevity.

    **1. Principle of Structure and Boundaries (Most Important Rule):**
    * **Fractions (`\\frac{{A}}{{B}}`):** Always explicitly announce the numerator and denominator. Use a structure like: "a fração com o numerador A e denominador B". **Never** use ambiguous terms like "A sobre B".
    * **Roots (`\\sqrt{{A}}`, `\\sqrt[n]{{A}}`):** Announce the beginning and end of the root's scope. Example: "a raiz quadrada de [content] fim da raiz" or "a raiz cúbica de [content] fim da raiz cúbica".
    * **Parentheses, Brackets, and Modulus:** Verbally announce the opening and closing of all delimiters. Example: "abre parênteses [content] fecha parênteses" or "o módulo de [content] fim do módulo".
    * **Integrals and Limits:** Describe the operator and its boundaries first before describing the main expression. Example: "a integral definida de A aa B de [expression]" or "o limite de x tendendo a A da [expression]".

    **2. Principle of Symbols and Operators:**
    * **Derivatives (Notation `f'`):** Consistently use the term "a derivada de". For higher orders (`f''`), use "a segunda derivada de", and so on. This applies to functions, variables, or entire expressions.
    * **Subscripts (`x_n`):** Always verbalize as "x índice n".
    * **Powers (`x^n`):** Use the form "x elevado à potência de n". For common exponents, "x ao quadrado" (`x^2`) and "x ao cubo" (`x^3`) are acceptable.
    * **Set Symbols:** Verbalize symbols with their full names: `∈` as "pertence a", `⊂` as "é um subconjunto de", `∩` as "interseção", `∀` as "para todo".
    * **Standard Number Sets:** Use the full names: `ℝ` (o conjunto dos números reais), `ℂ` (o conjunto dos números complexos), `ℤ` (o conjunto dos números inteiros).
    * **Function Mapping (`f: A \\to B`):** Describe as "a função f mapeia de A para B".
    * **Definition (`:=`):** Read as "é definido como".

    **3. Principle of Document Context:**
    * **Item Structure:** If the equation is part of a list or exercise with markers (e.g., (a), (b), 1., 2.), announce the item before describing the equation. Example: "Item a: [equation description]".
    * **Titles and Sections:** If there are titles or section headings (e.g., `\\section{{Average Speed}}`), announce them as such to give context to the listener.
    **[END OF EQUATION READING GUIDELINES]**
    ---

    * **MANDATORY PAIRING RULE: Every time you write a LaTeX equation inside `<span aria-hidden="true">...</span>`, it is MANDATORY that it be immediately followed by its corresponding natural language description inside `<span class="sr-only">...</span>`. THERE ARE NO EXCEPTIONS to this rule. The two elements must always appear together as a pair.**
    * **MANDATORY BLOCK STRUCTURE: The pair of <span> (visual equation and textual description) MUST be enclosed by a block-level paragraph element <p>: <p><span aria-hidden="true">...</span> <span class="sr-only">...</span></p>**
    * **CRITICAL DELIMITER USAGE:** For inline mathematics, YOU MUST USE `<span aria-hidden="true">\\(...\\)</span>` (e.g., `<span aria-hidden="true">\\(x=y\\)</span>`). For display mathematics (equations on their own line), YOU MUST USE `<span aria-hidden="true">$$...$$</span>` (e.g., `<span aria-hidden="true">$$x = \\sum y_i$$</span>`).
    * **Ensure that *all* mathematical symbols, including single-letter variables mentioned in prose (e.g., '...where v is velocity...'), are enclosed in inline LaTeX delimiters followed by a natural language description (e.g., output as '...where <span aria-hidden="true">\\(v\\)</span> <span class="sr-only">v</span> is velocity...').** This applies to all isolated symbols.
    * Exemple inline mathematics: <p>Se a posição de um carro no instante <span aria-hidden="true">\\(t > 0\\)</span> <span class="sr-only"> t maior que 0</span> é dada por <span aria-hidden="true">\\(s(t) = (4+t^2)\\)</span> <span class="sr-only">s de t é igual a 4 mais t ao quadrado</span></p>
    * Exemple display mathematics: <p><span aria-hidden="true">$$ v(2) = 4. $$</span> <span class="sr-only"> v de 2 é igual a 4</span></p>

4.  **Tables (CRITICAL FOR ACCESSIBILITY):**
    * Identify any tables.
    * **CRITICAL:** Extract the table's main title or header and place it inside a `<caption>` tag as the very first element within the `<table>`. Example: `<table><caption>Vendas Mensais por Região</caption>...</table>`. This provides essential context for screen reader users.
    * Format the table using proper HTML tags (`<table>`, `<thead>`, `<tbody>`, `<tr>`, `<th>`, `<td>`).
    * **Pay close attention to table structure:**
        * Correctly identify header cells and use the `<th>` tag for them.
        * For column and row headers, use the `scope` attribute (e.g., `<th scope="col">Nome da Coluna</th>`, `<th scope="row">Nome da Linha</th>`).
        * Accurately detect and represent merged cells using `colspan` for horizontally merged cells and `rowspan` for vertically merged cells.
    * **Example of a complex table structure:**
        ```html
        <table>
          <caption>Exemplo de Tabela Complexa</caption>
          <thead>
            <tr>
              <th scope="col">Produto</th>
              <th scope="col" colspan="2">Detalhes de Vendas</th>
            </tr>
            <tr>
              <th scope="col"></th>
              <th scope="col">Região A</th>
              <th scope="col">Região B</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th scope="row">Item 1</th>
              <td>100</td>
              <td>150</td>
            </tr>
            <tr>
              <th scope="row" rowspan="2">Itens Agrupados</th>
              <td>200</td>
              <td>210</td>
            </tr>
            <tr>
              <td>205</td>
              <td>215</td>
            </tr>
          </tbody>
        </table>
        ```

5.  **Hierarchy of Headings (NAVIGATION CRITICAL):**
    * Identify the document's structural hierarchy within the page content (e.g., section titles, sub-section titles).
    * **CRITICAL:** DO NOT create new titles or headings that do not exist in the original text.
    * Use `<h3>`, `<h4>`, `<h5>`, and `<h6>` tags to mark this hierarchy. A main section title on the page should be `<h3>`, a subsection within it `<h4>`, and so on.
    * **YOU MUST add a unique `id` to every heading you create.** Use the format `id="h{{LEVEL}}-{current_page_num_in_doc}-{{INDEX}}"`, where `{{LEVEL}}` is the heading number (3, 4, etc.) and `{{INDEX}}` is a sequential number for that heading level on the page (1, 2, 3...).
    * Example: `<h3 id="h3-{current_page_num_in_doc}-1">Primeira Seção</h3>`, `<h4 id="h4-{current_page_num_in_doc}-1">Primeira Subseção</h4>`.

6.  **Visual Elements (Descriptions):**
    * Identify significant diagrams, graphs, figures, or images relevant to the academic content. **DO NOT** describe purely decorative elements like logos that are not relevant to the understanding of the text.
    * **Instead of including the image itself, provide a concise textual description** in Portuguese, wrapped in `<p><em>...</em></p>`. The description should explain what the visual element shows and its relevance.
    * In the case of a bar code, QR code, or similar, **ALWAYS** indicate that it is there and describe its purpose using the `<p><em>...</em></p>` tag.
    * Example: `<p><em>[Descrição da imagem: Diagrama de um circuito elétrico RLC em série, mostrando a fonte de tensão, o resistor R, o indutor L e o capacitor C.]</em></p>`.

7.  **Footnotes (Notas de Rodapé):**
    * Identify footnote markers and their corresponding text.
    * Link them using the following precise patterns:
        * **In-text marker:** `<sup><a href="#fn{current_page_num_in_doc}-{{INDEX}}" id="fnref{current_page_num_in_doc}-{{INDEX}}" aria-label="Nota de rodapé {{INDEX}}">{{MARKER}}</a></sup>`
        * **Footnote list (at the very end of the page's HTML):**
            ```html
            <hr class="footnotes-separator" />
            <div class="footnotes-section">
              <h4 class="sr-only">Notas de Rodapé da Página {current_page_num_in_doc}</h4>
              <ol class="footnotes-list">
                <li id="fn{current_page_num_in_doc}-{{INDEX}}">TEXT_OF_THE_FOOTNOTE. <a href="#fnref{current_page_num_in_doc}-{{INDEX}}" aria-label="Voltar para a referência da nota de rodapé {{INDEX}}">&#8617;</a></li>
              </ol>
            </div>
            ```

8.  **Abbreviations and Acronyms:**
    * If you identify a known abbreviation or acronym (e.g., ABNT, PIB, DNA), use the `<abbr>` tag to provide its full expansion. This helps screen readers pronounce them correctly.
    * Example: `Segundo a <abbr title="Associação Brasileira de Normas Técnicas">ABNT</abbr>, a regra é...`

9.  **Final HTML Structure:**
    * Use semantic HTML.
    * **AVOID UNNECESSARY TAGS:** Do NOT use `<bdi>` tags. They are generally not needed for Portuguese or mathematical content and can interfere with screen readers.
    * Output ONLY the extracted content as HTML body content in a single Markdown code block.
    * **AVOID UNNECESSARY TAGS:** Do NOT use `<bdi>` tags unless there is a clear, demonstrable need for bi-directional text isolation. This is generally not required for mathematical variables or simple text in Portuguese.
**CRITICAL: Do NOT add any summary/explanation beyond original Portuguese. NO `<img>` tags.** Output only HTML code block.
"""
    return prompt


def get_html(pdf_filename_title: str, report_button: bool):
    report_button_css = ""
    report_button_js = ""
    report_button_js2 = ""
    report_button_html = ""
    report_button_instructions = ""
    report_button_forms = ""

    if report_button:
        report_button_css = """
        .modal {
            display: none; /* Oculto por padrão */
            position: fixed; 
            z-index: 2000; /* Fica sobre todo o conteúdo */
            left: 0;
            top: 0;
            width: 100%; 
            height: 100%; 
            overflow: auto; 
            background-color: rgba(0,0,0,0.6); 
        }
        .modal-content {
            margin: 15% auto;
            padding: 20px;
            border: 1px solid #888;
            width: 80%;
            max-width: 500px;
            border-radius: 5px;
        }
        .modal-content label { display: block; margin-top: 10px; }
        .modal-content input[type="text"], .modal-content textarea {
            width: 100%;
            padding: 8px;
            margin-top: 5px;
            box-sizing: border-box;
            border-radius: 3px;
            border: 1px solid #ccc;
        }
        .modal-content button[type="submit"] {
            padding: 10px 15px;
            margin-top: 15px;
            border: none;
            border-radius: 3px;
            cursor: pointer;
        }
        .close-button {
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        .close-button:hover, .close-button:focus { text-decoration: none; }

        /* Estilos do Modal para cada tema */
        body.normal-mode .modal-content { background-color: #fefefe; color: #333; }
        body.normal-mode .modal-content input, body.normal-mode .modal-content textarea { background-color: #fff; border-color: #ccc; color: #000; }
        body.normal-mode .modal-content button { background-color: #007BFF; color: white; }
        body.normal-mode .close-button { color: #aaa; }
        body.normal-mode .close-button:hover, body.normal-mode .close-button:focus { color: black; }
        
        body.dark-mode .modal-content { background-color: #2c2c2c; border-color: #555; color: #e0e0e0; }
        body.dark-mode .modal-content input, body.dark-mode .modal-content textarea { background-color: #333; border-color: #555; color: #e0e0e0; }
        body.dark-mode .modal-content button { background-color: #4dabf7; color: #000; }
        body.dark-mode .close-button { color: #ccc; }
        body.dark-mode .close-button:hover, body.dark-mode .close-button:focus { color: white; }

        body.high-contrast-mode .modal-content { background-color: #000; border: 2px solid #FFFF00; color: #FFFF00; }
        body.high-contrast-mode .modal-content input, body.high-contrast-mode .modal-content textarea { background-color: #111; border-color: #FFFF00; color: #FFFF00; }
        body.high-contrast-mode .modal-content button { background-color: #FFFF00; color: #000; }
        body.high-contrast-mode .close-button { color: #FFFF00; }
        """

        report_button_js = """
    // --- FUNÇÕES PARA RELATAR PROBLEMA ---
    /**
    * Envia os dados do relato para um Google Form via requisição fetch.
    * @param {string} filename - O nome do arquivo/documento.
    * @param {string} pages - As páginas com problema (ex: "1", "3-5").
    * @param {string} description - A descrição do problema.
    */
    async function submitReport(filename, pages, description) {
    // Estas informações devem ser extraídas do seu link do Google Forms
    const googleFormURL = 'https://docs.google.com/forms/d/e/1FAIpQLSceYTiU_ec4anxBzANdKc8RF1jPbGNxMET4P_ICm95FLTZa8w/formResponse';
    const entryFileName = 'entry.681517248';
    const entryPages = 'entry.57540117';
    const entryDescription = 'entry.1947389767';
    const entryTimestamp = 'entry.877859521';

    const formData = new FormData();
    formData.append(entryFileName, filename);
    formData.append(entryPages, pages);
    formData.append(entryDescription, description);
    formData.append(entryTimestamp, new Date().toLocaleString('pt-BR'));

    try {
        await fetch(googleFormURL, {
            method: 'POST',
            body: formData,
            mode: 'no-cors' // Essencial para evitar erros de CORS com o Google
        });
        alert('Relato enviado com sucesso! Obrigado pela sua contribuição.');
    } catch (error) {
        console.error('Erro ao enviar o formulário:', error);
        alert('Ocorreu um erro ao enviar o seu relato. Por favor, tente novamente.');
    }
    }

    /**
    * Obtém o nome do documento a partir do título H1 no cabeçalho.
    * @returns {string} O nome do documento.
    */
    function getDocumentName() {
    const titleElement = document.querySelector('header h1');
    if (titleElement) {
        const fullTitle = titleElement.textContent;
        // Ex: "Documento Acessível: max-min-solucao" -> "max-min-solucao"
        return fullTitle.split(': ')[1] || 'Documento Desconhecido';
    }
    return 'Documento Desconhecido';
    }

    /**
    * Encontra o número da página onde a seleção de texto do usuário está.
    * @param {Selection} selection - O objeto de seleção do window.
    * @returns {string} O número da página ou 'N/A' se não for encontrado.
    */
    function getPageNumberOfSelection(selection) {
    if (!selection || selection.rangeCount === 0) return 'N/A';
    const range = selection.getRangeAt(0);
    const container = range.commonAncestorContainer;
    const node = container.nodeType === 3 ? container.parentNode : container;
    const pageArticle = node.closest('article.page-content');
    if (pageArticle && pageArticle.id.startsWith('page-')) {
        return pageArticle.id.replace('page-', '');
    }
    return 'N/A';
    }

    /**
    * Função principal chamada pelo botão "Relatar Problema".
    * Verifica se há texto selecionado para decidir se envia o relato diretamente ou abre o modal.
    */
    async function handleReportProblem() {
    const selection = window.getSelection();
    const selectedText = selection.toString().trim();
    const documentName = getDocumentName();

    if (selectedText) {
        const pageNumber = getPageNumberOfSelection(selection);
        const description = `"${selectedText}"`; 

        const userConfirmed = confirm(
            `Você deseja relatar o seguinte problema?\n\n` +
            `Arquivo: ${documentName}\n` +
            `Página: ${pageNumber}\n` +
            `Texto: ${description}\n`
        );

        if (userConfirmed) {
            await submitReport(documentName, pageNumber, description);
        }
    } else {
        openReportModal();
    }
    }

    /** Abre e prepara o modal de relato. */
    function openReportModal() {
    const modal = document.getElementById('reportModal');
    if (!modal) return;
    const documentName = getDocumentName();
    document.getElementById('modalFileName').textContent = `Arquivo: ${documentName}`;
    document.getElementById('reportFileNameInput').value = documentName;
    modal.style.display = 'block';
    }

    /** Fecha e limpa o modal de relato. */
    function closeReportModal() {
    const modal = document.getElementById('reportModal');
    if (!modal) return;
    modal.style.display = 'none';
    const form = document.getElementById('reportForm');
    if (form) form.reset();
    }

    /** Inicializa os eventos do modal (fechar, enviar formulário). */
    function initializeReportModal() {
    const modal = document.getElementById('reportModal');
    if (!modal) return;

    const form = document.getElementById('reportForm');

    // O evento do botão de fechar já está no HTML (onclick="closeReportModal()")

    window.onclick = function(event) {
        if (event.target == modal) {
            closeReportModal();
        }
    }

    if (form) {
        form.addEventListener('submit', async (event) => {
            event.preventDefault();

            const submitButton = form.querySelector('button[type="submit"]');
            submitButton.textContent = 'Enviando...';
            submitButton.disabled = true;

            const filename = document.getElementById('reportFileNameInput').value;
            const pages = document.getElementById('problemPages').value;
            const description = document.getElementById('problemDescription').value;

            await submitReport(filename, pages, description);
            
            submitButton.textContent = 'Enviar Relato';
            submitButton.disabled = false;
            closeReportModal();
        });
    }
    }
        """

        report_button_js2 = "initializeReportModal();"

        report_button_html = """
        <div class="control-group">
            <span>Ajuda e Suporte:</span>
            <button id="reportProblemBtn" onclick="handleReportProblem()" aria-label="Relatar um problema com o documento">🐞 Relatar Problema</button>
        </div>
        """

        report_button_instructions = """<li><strong>Relatar um Problema:</strong> Encontrou um erro de formatação ou leitura? Selecione o texto problemático na página e clique no botão "🐞 Relatar Problema". O sistema preencherá o relatório para você. Se nenhum texto for selecionado, um formulário será aberto para preenchimento manual.</li>"""

        report_button_forms = """
        <div id="reportModal" class="modal">
            <div class="modal-content">
                <span class="close-button" onclick="closeReportModal()" title="Fechar">&times;</span>
                <h2>Relatar Problema com o Documento</h2>
                <h3 id="modalFileName"></h3>
                <form id="reportForm">
                    <input type="hidden" id="reportFileNameInput" name="filename">
                    <label for="problemPages">Página(s) com problema (ex: 1, 3-5):</label>
                    <input type="text" id="problemPages" name="pages" required>
                    <label for="problemDescription">Descrição do problema:</label>
                    <textarea id="problemDescription" name="description" rows="4" required></textarea>
                    <button type="submit" class="button">Enviar Relato</button>
                </form>
            </div>
        </div>
        """


    accessibility_css = """
    <style>
    html, body {margin: 0;padding: 0;overflow-x: auto;}
    body {font-family: Verdana, Arial, sans-serif; line-height: 1.6; padding: 20px; background-color: #f0f0f0; color: #333; transition: background-color 0.3s, color 0.3s;}
    #accessibility-controls {position: sticky; top: 0; z-index: 1000; padding: 10px; margin-bottom: 20px; border: 1px solid; border-radius: 5px; display: flex; flex-wrap: wrap; align-items: center; gap: 8px; box-sizing: border-box;}
    body.normal-mode #accessibility-controls:not(.expanded) {background-color: #e0e0e0; border-color: #ccc; color: #000;}
    body.dark-mode #accessibility-controls:not(.expanded) {background-color: #1e1e1e; border-color: #444; color: #fff;}
    body.high-contrast-mode #accessibility-controls:not(.expanded) {background-color: #000; border-color: #00FF00; color: #00FF00;}
    #accessibility-controls .control-group > button,
    #accessibility-controls .control-group > select,
    #accessibility-controls .control-group > label:not(:first-child),
    #accessibility-controls .control-group > input,
    #accessibility-controls .control-group > span:not(:first-child) {display: inline-flex; align-items: center; justify-content: center; white-space: normal; min-width: 0; word-break: break-all; flex-grow: 0; flex-shrink: 1; flex-basis: auto; max-width: 100%; padding: 5px 10px; border-radius: 3px; box-sizing: border-box; cursor: pointer; text-align: center; margin: 0;}
    #accessibility-controls .control-group > *:first-child {width: 100%; flex-shrink: 0; box-sizing: border-box; margin-bottom: 8px; font-weight: bold; white-space: normal; word-break: break-word;}
    #accessibility-toggle img {pointer-events: none;}
    .page-content {padding: 15px; margin-bottom: 20px; border: 1px solid; border-radius: 3px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);}
    body.normal-mode {background-color: #f0f0f0; color: #333;}
    body.normal-mode .page-content {background-color: #ffffff;border-color: #dddddd;}
    body.normal-mode h1, body.normal-mode h2 { color: #000; border-color: #eee;}
    body.normal-mode p i, body.normal-mode span i, body.normal-mode p em, body.normal-mode span em { color: #555555 !important; }
    body.normal-mode sup > a { color: #0066cc; }
    body.normal-mode hr.page-separator { border-color: #ccc; }
    body.normal-mode hr.footnotes-separator { border-color: #ccc; }
    body.normal-mode #accessibility-controls.expanded {background-color: #f0f0f0; border-color: #ccc; color: #000;}
    body.normal-mode #accessibility-controls button, body.normal-mode #accessibility-controls select { background-color: #fff; border: 1px solid #bbb; color: #000; }
    body.dark-mode {background-color: #121212; color: #e0e0e0;}
    body.dark-mode .page-content {background-color: #1e1e1e;border-color: #444444;}
    body.dark-mode h1, body.dark-mode h2 {color: #ffffff; border-color: #444;}
    body.dark-mode p i, body.dark-mode span i, body.dark-mode p em, body.dark-mode span em { color: #AAAAAA !important; }
    body.dark-mode sup > a { color: #87CEFA; }
    body.dark-mode hr.page-separator { border-color: #555; }
    body.dark-mode hr.footnotes-separator { border-color: #555; }
    body.dark-mode #accessibility-controls.expanded {background-color: #2c2c2c; border-color: #555; color: #e0e0e0;}
    body.dark-mode #accessibility-controls button, body.dark-mode #accessibility-controls select { background-color: #333; border: 1px solid #555; color: #e0e0e0; }
    body.high-contrast-mode {background-color: #000000;color: #FFFF00;}
    body.high-contrast-mode .page-content {background-color: #000000;border: 2px solid #FFFF00;}
    body.high-contrast-mode h1, body.high-contrast-mode h2 {color: #FFFF00; border-color: #FFFF00;}
    body.high-contrast-mode p, body.high-contrast-mode span, body.high-contrast-mode li, body.high-contrast-mode td, body.high-contrast-mode th { color: #FFFF00 !important; }
    body.high-contrast-mode p i, body.high-contrast-mode span i, body.high-contrast-mode p em, body.high-contrast-mode span em {color: #01FF01 !important;}
    body.high-contrast-mode sup > a { color: #00FFFF; text-decoration: underline; }
    body.high-contrast-mode hr.page-separator { border: 2px dashed #FFFF00; }
    body.high-contrast-mode hr.footnotes-separator { border: 1px dotted #FFFF00; }
    body.high-contrast-mode #accessibility-controls.expanded {background-color: #000; border-color: #FFFF00; color: #FFFF00;}
    body.high-contrast-mode #accessibility-controls button, body.high-contrast-mode #accessibility-controls select { background-color: #111; color: #FFFF00; border: 1px solid #FFFF00;}
    h1 { font-size: 2em; border-bottom: 2px solid; padding-bottom: 0.3em; margin-top: 1em; margin-bottom: 0.5em; }
    h2 { font-size: 1.75em; border-bottom: 1px solid; padding-bottom: 0.3em; margin-top: 1em; margin-bottom: 0.5em;}
    hr.page-separator { margin-top: 2.5em; margin-bottom: 2.5em; border-width: 0; border-top: 2px dashed; }
    hr.footnotes-separator { margin-top: 1.5em; margin-bottom: 1em; border-style: dotted; border-width: 1px 0 0 0; }
    .footnotes-section { margin-top: 1em; padding-top: 0.5em; font-size: 0.9em; }
    .footnotes-list { list-style-type: decimal; padding-left: 25px; }
    .footnotes-list li { margin-bottom: 0.5em; }
    .footnotes-list li a { text-decoration: none; margin-left: 5px;}
    .footnotes-list li a:hover { text-decoration: underline; }
    .sr-only {
        opacity: 0;
        height: 1px;
        width: 1px;
        overflow: hidden;
        display: inline-block;
        white-space: nowrap;
        border: 0;
        padding: 0;
        margin: 0;
    }
    p i, span i {font-style: italic;}
    sup > a {text-decoration: none;} sup > a:hover {text-decoration: underline;}
    table { border-collapse: collapse; width: auto; margin: 1em 0; }
    th, td { border: 1px solid; padding: 0.5em; text-align: left; }
    body.normal-mode th, body.normal-mode td { border-color: #ccc; }
    body.dark-mode th, body.dark-mode td { border-color: #555; }
    body.high-contrast-mode th, body.high-contrast-mode td { border-color: #FFFF00; }
    .MathJax_Display { margin: 1em 0 !important; }
    #accessibility-toggle { position: fixed; top: 20px; right: 20px; z-index: 1100; width: 50px; height: 50px; background-color: #007BFF; color: white; border: none; border-radius: 50%; font-size: 24px; cursor: pointer; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2); }
    body.dark-mode #accessibility-toggle { background-color: #4dabf7; }
    body.high-contrast-mode #accessibility-toggle { background-color: #FFFF00; color: #000; border: 1px solid #000;}
    body.high-contrast-mode #accessibility-toggle img { filter: invert(1) brightness(0.8); }
    #accessibility-controls.collapsed { display: none; }
    #accessibility-controls.expanded {position: fixed; top: 80px; right: 20px; width: 100%; max-width: 360px; box-sizing: border-box; overflow: auto; max-height: calc(100vh - 100px);}
    .control-group {display: flex; flex-wrap: wrap; align-items: center; gap: 8px; padding: 10px; margin-bottom: 15px; border: 1px solid; border-radius: 4px; box-sizing: border-box;}
    body.normal-mode .control-group { border-color: #bbb; }
    body.dark-mode .control-group { border-color: #555; }
    body.high-contrast-mode .control-group { border-color: #FFFF00; }
    details.original-page-viewer { margin-top: 20px; margin-bottom: 20px; border: 1px dashed #999; border-radius: 5px; padding: 10px; background-color: rgba(0,0,0,0.02); }
    body.dark-mode details.original-page-viewer { border-color: #666; background-color: rgba(255,255,255,0.03); }
    body.high-contrast-mode details.original-page-viewer { border-color: #FFFF00; background-color: #111; }
    details.original-page-viewer summary { cursor: pointer; padding: 8px; font-weight: bold; color: #0056b3; background-color: rgba(0,0,0,0.03); border-radius: 3px; margin: -10px -10px 10px -10px; }
    body.dark-mode details.original-page-viewer summary { color: #87CEFA; background-color: rgba(255,255,255,0.05); }
    body.high-contrast-mode details.original-page-viewer summary { color: #00FFFF; background-color: #222; border: 1px solid #FFFF00; }
    details.original-page-viewer summary:hover, details.original-page-viewer summary:focus { text-decoration: underline; background-color: rgba(0,0,0,0.05); }
    body.dark-mode details.original-page-viewer summary:hover, body.dark-mode details.original-page-viewer summary:focus { background-color: rgba(255,255,255,0.08); }
    body.high-contrast-mode details.original-page-viewer summary:hover, body.high-contrast-mode details.original-page-viewer summary:focus { background-color: #333; }
    details.original-page-viewer img { display: block; max-width: 100%; height: auto; margin-top: 10px; border: 1px solid #ccc; background-color: white; }
    body.dark-mode details.original-page-viewer img { border-color: #444; background-color: #333; }
    body.high-contrast-mode details.original-page-viewer img { border-color: #FFFF00; background-color: #000; }
    .tts-highlight { background-color: yellow !important; color: black !important; box-shadow: 0 0 8px rgba(218, 165, 32, 0.7); transition: background-color 0.2s ease-in-out, color 0.2s ease-in-out; border-radius: 3px; }
    .dark-mode .tts-highlight { background-color: #58a6ff; }
    .high-contrast-mode .tts-highlight { background-color: #FFFF00; color: black !important; }
    .tts-paused { background-color: lightblue !important; color: black !important; border-radius: 3px; transition: background-color 0.2s ease-in-out; }
    .dark-mode .tts-paused { background-color: #005f99 !important; }
    .high-contrast-mode .tts-paused { background-color: #00FFFF !important; color: black !important; }
    .high-contrast-mode .tts-highlight [aria-hidden="true"] * {color: black !important; fill: black !important;}
    #recenter-slider-container {display: none; margin-left: auto; align-items: center; gap: 8px;}
    #recenter-slider-container.active {display: flex; width: 300px;}
    #recenterIntervalSlider {flex: 1; min-width: 50px;}
    #recenterIntervalValue {min-width: 200px; text-align: right; font-variant-numeric: tabular-nums;}
    """ + f""" {report_button_css}
    </style>
    """


    accessibility_js = f"""
    <script>
    {report_button_js}
    """ + r"""
    // --- CONFIGURAÇÃO E ESTADO GLOBAL ---
    let currentFontSize = 16;
    const fonts = ['Atkinson Hyperlegible', 'Lexend', 'OpenDyslexicRegular', 'Verdana', 'Arial', 'Times New Roman', 'Courier New'];
    let currentFontIndex = 0;

    const synth = window.speechSynthesis;
    let voices = [];
    let utterance = null;
    let isPaused = false;

    // Estado da fila de leitura
    let speechQueue = [];
    let currentSegmentIndex = 0;
    let currentlyHighlightedElement = null;

    // Estado da recentralização periódica
    let isPeriodicRecenterEnabled = false;
    let recenterInterval = null;
    let recenterIntervalTime = 1000;

    // flags para race conditions
    let endedWhilePaused = false;
    let userInitiatedPause = false;
    let utteranceSegmentIndex = -1;


    // --- FUNÇÕES DE SÍNTESE DE VOZ E PROCESSAMENTO DE TEXTO ---

    function processTable(tableNode) {
    let content = [];
    const caption = tableNode.querySelector('caption');
    if (caption && caption.innerText.trim()) { content.push(`Iniciando tabela com título: ${caption.innerText.trim()}.`); } else { content.push("Iniciando tabela."); }
    const headers = [];
    const firstRow = tableNode.querySelector('tr');
    if (firstRow) { firstRow.querySelectorAll('th').forEach(th => { headers.push(th.innerText.trim()); }); }
    const allRows = Array.from(tableNode.querySelectorAll('tr'));
    const bodyRows = headers.length > 0 ? allRows.slice(1) : allRows;
    bodyRows.forEach(row => {
        let rowContent = [];
        const rowHeader = row.querySelector('th');
        if (rowHeader && rowHeader.innerText.trim()) { rowContent.push(`Linha: ${rowHeader.innerText.trim()}.`); }
        const cells = row.querySelectorAll('td');
        cells.forEach((cell, index) => {
            const headerText = headers[index] || `Coluna ${index + 1}`;
            const cellText = cell.innerText.trim();
            if (cellText) { rowContent.push(`${headerText}: ${cellText}.`); }
        });
        if (rowContent.length > 0) { content.push(rowContent.join(' ')); }
    });
    if (content.length <= 1) {
        const fallbackText = tableNode.innerText.trim().replace(/\s+/g, ' ');
        if (fallbackText) { return { text: "Tabela encontrada. Conteúdo: " + fallbackText, element: tableNode }; } else { return { text: "Tabela encontrada, mas está vazia.", element: tableNode }; }
    }
    return { text: content.join(' '), element: tableNode };
    }

    function populateVoiceList() {
    voices = synth.getVoices().sort((a, b) => a.lang.localeCompare(b.lang));
    const voiceSelector = document.getElementById('voiceSelector');
    if (!voiceSelector) return;
    voiceSelector.innerHTML = '';
    const ptVoices = voices.filter(voice => voice.lang.startsWith('pt'));
    const enVoices = voices.filter(voice => voice.lang.replace("_","-").startsWith('en-US'));
    const sortedVoices = [...ptVoices, ...enVoices];
    sortedVoices.forEach(voice => {
        const option = document.createElement('option');
        option.textContent = `${voice.name} (${voice.lang})`;
        option.setAttribute('data-lang', voice.lang);
        option.setAttribute('data-name', voice.name);
        voiceSelector.appendChild(option);
    });
    const savedVoiceName = localStorage.getItem('accessibilityVoiceName');
    if (savedVoiceName) {
        const savedOption = Array.from(voiceSelector.options).find(opt => opt.textContent.includes(savedVoiceName));
        if (savedOption) savedOption.selected = true;
    }
    }

    function toRoman(num) {
    if (num < 1 || num > 3999) return num.toString(); // Limita a conversão a um intervalo razoável
    const roman = { M: 1000, CM: 900, D: 500, CD: 400, C: 100, XC: 90, L: 50, XL: 40, X: 10, IX: 9, V: 5, IV: 4, I: 1 };
    let str = '';
    for (let i of Object.keys(roman)) {
        let q = Math.floor(num / roman[i]);
        num -= q * roman[i];
        str += i.repeat(q);
    }
    return str;
    }


    function getListPrefix(liElement) {
    const parentList = liElement.closest('ol, ul');
    if (!parentList) {
        return 'Item: ';
    }

    const listItems = Array.from(parentList.children).filter(child => child.tagName === 'LI');
    const index = listItems.indexOf(liElement);

    if (parentList.tagName === 'OL') {
        const type = parentList.getAttribute('type') || '1';
        const start = parseInt(parentList.getAttribute('start'), 10) || 1;
        const displayNumber = start + index;

        switch (type) {
            case 'a': // a, b, c...
                // 97 é o código do caractere 'a'
                return `Item ${String.fromCharCode(97 + index)}: `;
            case 'A': // A, B, C...
                // 65 é o código do caractere 'A'
                return `Item ${String.fromCharCode(65 + index)}: `;
            case 'i': // i, ii, iii...
                return `Item ${toRoman(displayNumber).toLowerCase()}: `;
            case 'I': // I, II, III...
                return `Item ${toRoman(displayNumber)}: `;
            case '1': // 1, 2, 3... (padrão)
            default:
                return `Item ${displayNumber}: `;
        }
    } else {
        return 'Marcador: ';
    }
    }


    function getLiTextOnly(liNode) {
    const clone = liNode.cloneNode(true);
    clone.querySelectorAll('p, ol, ul, blockquote, table, h1, h2, h3, h4, h5, h6').forEach(el => el.remove());
    clone.querySelectorAll('[aria-hidden="true"]').forEach(el => el.remove());
    return (clone.textContent || '').trim().replace(/\s+/g, ' ');
    }


    function extractContentWithSemantics(rootNode) {
    const segments = [];
    const elementsToProcess = rootNode.querySelectorAll('p, h1, h2, h3, h4, h5, h6, li, blockquote, table');
    const spokenLiPrefixes = new Set();

    elementsToProcess.forEach(node => {
        if ((node.closest('table') && node.tagName !== 'TABLE') || node.closest('[aria-hidden="true"]')) { return; }
        if (node.tagName === 'TABLE') {
            const tableSegment = processTable(node);
            if (tableSegment && tableSegment.text) segments.push(tableSegment);
            return;
        }

        let text = '';
        let prefix = '';

        if (node.tagName === 'LI') {
            text = getLiTextOnly(node);
        } else {
            const clone = node.cloneNode(true);
            clone.querySelectorAll('[aria-hidden="true"]').forEach(el => el.remove());
            text = (clone.textContent || '').trim().replace(/\s+/g, ' ');
        }

        if (!text) {
            return;
        }

        const parentLi = node.closest('li');
        if (parentLi && !spokenLiPrefixes.has(parentLi)) {
            prefix = getListPrefix(parentLi);
            spokenLiPrefixes.add(parentLi);
        }

        segments.push({ text: prefix ? prefix + text : text, element: node });
    });

    return segments;
    }

    function speakText() {
    if (synth.speaking && !isPaused) return;

    if (synth.paused && utterance && !endedWhilePaused) {
        try { synth.resume(); } catch (e) { console.warn('resume falhou', e); }
        return;
    }

    if (endedWhilePaused) {
        endedWhilePaused = false;
        try { synth.cancel(); } catch (e) { /* ignore */ }

        if (currentlyHighlightedElement) {
            currentlyHighlightedElement.classList.remove('tts-highlight', 'tts-paused');
            currentlyHighlightedElement = null;
        }

        if (currentSegmentIndex < speechQueue.length) {
            playQueue();
        } else {
            stopSpeech();
        }
        return;
    }

    if (speechQueue.length > 0 && currentSegmentIndex < speechQueue.length) {
        playQueue();
        return;
    }

    speechQueue = [];
    currentSegmentIndex = 0;

    const selection = window.getSelection();
    const selectedText = selection.toString().trim();

    if (selectedText && selection.rangeCount > 0) {
        let combinedFragment = document.createDocumentFragment();
        for (let i = 0; i < selection.rangeCount; i++) { combinedFragment.appendChild(selection.getRangeAt(i).cloneContents()); }
        const container = document.createElement('div');
        container.appendChild(combinedFragment);
        const hasBlocks = !!container.querySelector('p, h1, h2, h3, h4, h5, h6, li, blockquote, table');
        if (!hasBlocks) {
            const wrapperP = document.createElement('p');
            wrapperP.appendChild(container.firstChild || document.createTextNode(selection.toString()));
            container.appendChild(wrapperP);
        }
        speechQueue = extractContentWithSemantics(container);
        if (speechQueue.length > 0) { speechQueue[0].text = "Texto selecionado: " + speechQueue[0].text; }
    } else {
        const rootNode = document.getElementById('main-content') || document.body;
        speechQueue = extractContentWithSemantics(rootNode);
    }

    if (speechQueue.length === 0) return;

    // timer de recentralização
    if (recenterInterval) { clearInterval(recenterInterval); recenterInterval = null; }
    if (isPeriodicRecenterEnabled) {
        recenterInterval = setInterval(() => {
            if (currentlyHighlightedElement && synth.speaking && !isPaused) {
                currentlyHighlightedElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }, recenterIntervalTime);
    }

    currentSegmentIndex = 0;
    playQueue();
    }

    function playQueue() {
    if (currentSegmentIndex >= speechQueue.length) { stopSpeech(); return; }

    if (synth.speaking && !isPaused) {
        return;
    }

    const segment = speechQueue[currentSegmentIndex];
    if (!segment || !segment.text) { currentSegmentIndex++; playQueue(); return; }

    if (currentlyHighlightedElement) { currentlyHighlightedElement.classList.remove('tts-highlight', 'tts-paused'); }

    if (segment.element) {
        currentlyHighlightedElement = segment.element;
        currentlyHighlightedElement.classList.add('tts-highlight');
        currentlyHighlightedElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    utterance = new SpeechSynthesisUtterance(segment.text);
    utteranceSegmentIndex = currentSegmentIndex;

    const voiceSelector = document.getElementById('voiceSelector');
    if (voiceSelector) {
        const selectedIndex = voiceSelector.selectedIndex;
        const selectedOption = voiceSelector.options[selectedIndex];
        if (selectedOption) {
            const voiceName = selectedOption.getAttribute('data-name');
            utterance.voice = voices.find(v => v.name === voiceName) || null;
        }
    }

    const rateSlider = document.getElementById('rateSlider');
    const pitchSlider = document.getElementById('pitchSlider');
    if (rateSlider) utterance.rate = parseFloat(rateSlider.value) || 1;
    if (pitchSlider) utterance.pitch = parseFloat(pitchSlider.value) || 1;

    utterance.onerror = (event) => {
        console.error('SpeechSynthesisUtterance.onerror', event);
        if (currentlyHighlightedElement) currentlyHighlightedElement.classList.remove('tts-highlight', 'tts-paused');
    };

    utterance.onpause = () => {
        isPaused = true;
        if (currentlyHighlightedElement) {
            currentlyHighlightedElement.classList.remove('tts-highlight');
            currentlyHighlightedElement.classList.add('tts-paused');
        }
    };

    utterance.onresume = () => {
        isPaused = false;
        userInitiatedPause = false;
        if (currentlyHighlightedElement) {
            currentlyHighlightedElement.classList.remove('tts-paused');
            currentlyHighlightedElement.classList.add('tts-highlight');
        }
    };

    utterance.onend = () => {
        utterance = null;

        if (userInitiatedPause || isPaused || synth.paused) {
            endedWhilePaused = true;
            if (utteranceSegmentIndex === currentSegmentIndex) {
                currentSegmentIndex++;
            }
            userInitiatedPause = false;
            return;
        }

        currentSegmentIndex++;
        playQueue();
    };

    isPaused = false;
    userInitiatedPause = false;
    try {
        synth.speak(utterance);
    } catch (e) {
        console.error('synth.speak falhou:', e);
    }
    }

    function speakFromVisible() {
    stopSpeech();

    const rootNode = document.getElementById('main-content') || document.body;
    speechQueue = extractContentWithSemantics(rootNode);

    if (speechQueue.length === 0) return;

    const viewportCenter = window.innerHeight / 2;
    let startIndex = 0;
    let bestDistance = Infinity;

    for (let i = 0; i < speechQueue.length; i++) {
        const el = speechQueue[i].element;
        if (el) {
            const rect = el.getBoundingClientRect();
            
            const elementCenter = (rect.top + rect.bottom) / 2;

            if (rect.bottom > 0 && rect.top < window.innerHeight) {
                const distance = Math.abs(elementCenter - viewportCenter);
                if (distance < bestDistance) {
                    bestDistance = distance;
                    startIndex = i;
                }
            }
        }
    }

    if (recenterInterval) { clearInterval(recenterInterval); recenterInterval = null; }
    if (isPeriodicRecenterEnabled) {
        recenterInterval = setInterval(() => {
            if (currentlyHighlightedElement && synth.speaking && !isPaused) {
                currentlyHighlightedElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }, recenterIntervalTime);
    }

    currentSegmentIndex = startIndex;
    playQueue();
    }

    function pauseSpeech() {
    if (synth.speaking && !synth.paused) {
        userInitiatedPause = true;
        isPaused = true;
        try { synth.pause(); } catch (e) { console.warn('pause falhou', e); }
    }
    }

    function stopSpeech() {
    if (utterance) utterance.onend = null;
    isPaused = false;
    userInitiatedPause = false;
    endedWhilePaused = false;
    utteranceSegmentIndex = -1;
    try { synth.cancel(); } catch (e) { /* ignore */ }
    if (currentlyHighlightedElement) { currentlyHighlightedElement.classList.remove('tts-highlight', 'tts-paused'); currentlyHighlightedElement = null; }
    if (recenterInterval) { clearInterval(recenterInterval); recenterInterval = null; }
    speechQueue = [];
    currentSegmentIndex = 0;
    utterance = null;
    }

    function skipToPrevious() {
    if (speechQueue.length === 0 || currentSegmentIndex <= 0) return;
    currentSegmentIndex = Math.max(0, currentSegmentIndex - 1);
    if (utterance) utterance.onend = null;
    try { synth.cancel(); } catch (e) {}
    setTimeout(() => { playQueue(); }, 80);
    }

    function skipToNext() {
    if (speechQueue.length === 0) { stopSpeech(); return; }
    if (currentSegmentIndex >= speechQueue.length - 1) { stopSpeech(); return; }
    currentSegmentIndex++;
    if (utterance) utterance.onend = null;
    try { synth.cancel(); } catch (e) {}
    setTimeout(() => { playQueue(); }, 80);
    }

    function updateFontSizeDisplay() {
    const fontSizeValue = document.getElementById('fontSizeValue');
    if (fontSizeValue) fontSizeValue.textContent = `${currentFontSize}px`;
    }

    function changeFontSize(delta) {
    currentFontSize += delta;
    if (currentFontSize < 10) currentFontSize = 10;
    if (currentFontSize > 48) currentFontSize = 48;
    document.body.style.fontSize = currentFontSize + 'px';
    localStorage.setItem('accessibilityFontSize', currentFontSize);
    updateFontSizeDisplay();
    if (currentlyHighlightedElement) { currentlyHighlightedElement.scrollIntoView({ behavior: 'smooth', block: 'center' }); }
    }

    function setFontFamily(fontName) {
    document.body.style.fontFamily = fontName + ', sans-serif';
    localStorage.setItem('accessibilityFontFamily', fontName);
    }

    function changeTheme(themeName) {
    const validThemes = ['normal', 'dark', 'high-contrast'];
    if (!validThemes.includes(themeName)) themeName = 'dark';
    document.body.className = '';
    document.body.classList.add(themeName + '-mode');
    localStorage.setItem('accessibilityTheme', themeName);
    }

    function updateSliderLabels() {
    const rateSlider = document.getElementById('rateSlider');
    const rateValue = document.getElementById('rateValue');
    const pitchSlider = document.getElementById('pitchSlider');
    const pitchValue = document.getElementById('pitchValue');
    if(rateValue && rateSlider) rateValue.textContent = `${parseFloat(rateSlider.value).toFixed(1)}x`;
    if(pitchValue && pitchSlider) pitchValue.textContent = parseFloat(pitchSlider.value).toFixed(1);
    if(rateValue && rateSlider) rateValue.textContent = `${parseFloat(rateSlider.value).toFixed(1)}x`;
    if(pitchValue && pitchSlider) pitchValue.textContent = parseFloat(pitchSlider.value).toFixed(1);
    if(recenterIntervalValue && recenterIntervalSlider) recenterIntervalValue.textContent = `${recenterIntervalSlider.value}ms`;
    }

    function saveSpeechSettings() {
    const voiceSelector = document.getElementById('voiceSelector');
    if (voiceSelector) { const selectedVoice = voiceSelector.options[voiceSelector.selectedIndex]; if (selectedVoice) { localStorage.setItem('accessibilityVoiceName', selectedVoice.getAttribute('data-name')); } }
    const rate = document.getElementById('rateSlider');
    const pitch = document.getElementById('pitchSlider');
    const recenterIntervalSlider = document.getElementById('recenterIntervalSlider');
    if (rate) localStorage.setItem('accessibilityRate', rate.value);
    if (pitch) localStorage.setItem('accessibilityPitch', pitch.value);
    if (recenterIntervalSlider) localStorage.setItem('accessibilityRecenterInterval', recenterIntervalSlider.value);
    }

    function toggleAccessibilityMenu() {
    const menu = document.getElementById('accessibility-controls');
    const toggleButton = document.getElementById('accessibility-toggle');
    const isExpanded = menu.classList.toggle('expanded');
    menu.classList.toggle('collapsed', !isExpanded);
    toggleButton.setAttribute('aria-expanded', isExpanded.toString());
    toggleButton.setAttribute('aria-label', isExpanded ? 'Fechar Menu de Acessibilidade' : 'Abrir Menu de Acessibilidade');
    }

    function togglePeriodicRecenter(isEnabled) {
    isPeriodicRecenterEnabled = isEnabled;
    localStorage.setItem('accessibilityRecenter', isEnabled);
    const sliderContainer = document.getElementById('recenter-slider-container');
    if (sliderContainer) {
        sliderContainer.classList.toggle("active", isEnabled);
    }

    if (recenterInterval) {
        clearInterval(recenterInterval);
        recenterInterval = null;
    }
    if (isEnabled && synth.speaking && !isPaused) {
        recenterInterval = setInterval(() => {
            if (currentlyHighlightedElement) {
                currentlyHighlightedElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }, recenterIntervalTime);
    }
    }

    function handleRecenterIntervalChange() {
    const slider = document.getElementById('recenterIntervalSlider');
    if (!slider) return;

    recenterIntervalTime = parseInt(slider.value, 10);
    updateSliderLabels();
    saveSpeechSettings();

    // Se o intervalo já estiver ativo, reinicia com o novo tempo
    if (recenterInterval) {
        clearInterval(recenterInterval);
        recenterInterval = setInterval(() => {
            if (currentlyHighlightedElement && synth.speaking && !isPaused) {
                currentlyHighlightedElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }, recenterIntervalTime);
    }
    }

    document.addEventListener('DOMContentLoaded', () => {
    if (synth.onvoiceschanged !== undefined) { synth.onvoiceschanged = populateVoiceList; }
    populateVoiceList();
    const savedTheme = localStorage.getItem('accessibilityTheme') || 'dark';
    changeTheme(savedTheme);
    const themeSelector = document.getElementById('themeSelector');
    if (themeSelector) themeSelector.value = savedTheme;
    const savedFontSize = parseInt(localStorage.getItem('accessibilityFontSize'), 10) || 16;
    currentFontSize = savedFontSize;
    document.body.style.fontSize = currentFontSize + 'px';
    updateFontSizeDisplay();
    const savedFontFamily = localStorage.getItem('accessibilityFontFamily') || fonts[0];
    setFontFamily(savedFontFamily);
    const fontSelector = document.getElementById('fontSelector');
    if (fontSelector) fontSelector.value = savedFontFamily;
    const savedRate = localStorage.getItem('accessibilityRate') || '1';
    const rateSlider = document.getElementById('rateSlider');
    if (rateSlider) rateSlider.value = savedRate;
    const savedPitch = localStorage.getItem('accessibilityPitch') || '1';
    const pitchSlider = document.getElementById('pitchSlider');
    if (pitchSlider) pitchSlider.value = savedPitch;
    const savedRecenter = localStorage.getItem('accessibilityRecenter') === 'true';
    isPeriodicRecenterEnabled = savedRecenter;
    const recenterToggle = document.getElementById('recenterToggle');
    if (recenterToggle) recenterToggle.checked = savedRecenter;
    const savedInterval = localStorage.getItem('accessibilityRecenterInterval') || '1000';
    recenterIntervalTime = parseInt(savedInterval, 10);
    const recenterIntervalSlider = document.getElementById('recenterIntervalSlider');
    if (recenterIntervalSlider) recenterIntervalSlider.value = savedInterval;
    const recenterSliderContainer = document.getElementById('recenter-slider-container');
    if (recenterSliderContainer) {
        recenterSliderContainer.style.display = ''; 
        recenterSliderContainer.classList.toggle('active', savedRecenter);
    }
    updateSliderLabels();
    document.addEventListener('keydown', function(event) { if (event.key === "Escape") { stopSpeech(); } });
    const menu = document.getElementById('accessibility-controls');
    const toggleButton = document.getElementById('accessibility-toggle');
    if (menu && !menu.classList.contains('expanded')) { menu.classList.add('collapsed'); }
    if (toggleButton && menu) { const isExpanded = menu.classList.contains('expanded'); toggleButton.setAttribute('aria-expanded', isExpanded.toString()); toggleButton.setAttribute('aria-label', isExpanded ? 'Fechar Menu de Acessibilidade' : 'Abrir Menu de Acessibilidade'); }
    """ + report_button_js2 + """
    });
    </script>
    """
    safe_title = html.escape(pdf_filename_title if pdf_filename_title else "Documento")
    mathjax_config_head_merged = f"""
    <head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Accessible Document: {safe_title}</title>
    <script>
    MathJax = {{
        tex: {{ inlineMath: [['\\\\(', '\\\\)']], displayMath: [['$$', '$$']], processEscapes: true, processEnvironments: true, tags: 'ams' }},
        options: {{ skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'], ignoreHtmlClass: 'tex2jax_ignore', processHtmlClass: 'tex2jax_process' }},
        svg: {{ fontCache: 'global' }}
    }};
    </script>
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js" id="MathJax-script" async></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400;1,700&family=Lexend:wght@100..900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/antijingoist/open-dyslexic@master/open-dyslexic-regular.css">
    {accessibility_css}
    {accessibility_js}
    </head>
    """

    safe_h1_title = html.escape(pdf_filename_title if pdf_filename_title else "Documento")
    merged_html = f"""<!DOCTYPE html>
    <html lang="pt-BR">
    {mathjax_config_head_merged}
    <body class="dark-mode"> <header role="banner"><h1>Documento Acessível: {safe_h1_title}</h1></header>
    <button id="accessibility-toggle" onclick="toggleAccessibilityMenu()" aria-label="Abrir Menu de Acessibilidade" aria-expanded="false">
        <img src="https://cdn.userway.org/widgetapp/images/body_wh.svg" alt="" style="width: 130%; height: 130%;"/>
    </button>

    <div id="accessibility-controls" class="collapsed" role="region" aria-labelledby="accessibility-menu-heading">
        <h2 id="accessibility-menu-heading" class="sr-only">Menu de Controles de Acessibilidade</h2>
        <div class="control-group">
            <span>Tamanho da Fonte: <span id="fontSizeValue" aria-live="polite">16px</span></span>
            <button onclick="changeFontSize(-2)" aria-label="Diminuir tamanho da fonte">A-</button>
            <button onclick="changeFontSize(2)" aria-label="Aumentar tamanho da fonte">A+</button>
        </div>
        <div class="control-group">
            <label for="fontSelector">Fonte:</label>
            <select id="fontSelector" onchange="setFontFamily(this.value)" aria-label="Selecionar família da fonte">
                <option value="Atkinson Hyperlegible">Atkinson Hyperlegible</option><option value="Lexend">Lexend</option>
                <option value="OpenDyslexicRegular">OpenDyslexic</option><option value="Verdana">Verdana</option>
                <option value="Arial">Arial</option><option value="Times New Roman">Times New Roman</option>
                <option value="Courier New">Courier New</option>
            </select>
        </div>
        <div class="control-group">
            <label for="themeSelector">Tema Visual:</label>
            <select id="themeSelector" onchange="changeTheme(this.value)" aria-label="Selecionar tema visual">
                <option value="normal">Modo Claro</option>
                <option value="dark">Modo Escuro</option>
                <option value="high-contrast">Alto Contraste</option>
            </select>
        </div>
        <div class="control-group">
            <span>Leitura em Voz Alta:</span>
            <button onclick="speakText()" aria-label="Ler ou continuar leitura">▶️ Ler/Continuar</button>
            <button onclick="speakFromVisible()" aria-label="Ler a partir do texto visível">🎯 Ler daqui</button>
            <button onclick="pauseSpeech()" aria-label="Pausar leitura">⏸️ Pausar</button>
            <button onclick="stopSpeech()" aria-label="Parar leitura (Tecla Esc)">⏹️ Parar (Esc)</button>
        </div>
        <div class="control-group">
            <span>Navegar no Texto:</span>
            <button onclick="skipToPrevious()" aria-label="Ler segmento anterior">⏪ Anterior</button>
            <button onclick="skipToNext()" aria-label="Ler próximo segmento">Próximo ⏩</button>
        </div>
        <div class="control-group">
            <label for="recenterToggle">Manter texto centralizado:</label>
            <input type="checkbox" id="recenterToggle" onchange="togglePeriodicRecenter(this.checked)" aria-label="Ativar ou desativar a centralização automática durante a leitura">
            
            <div id="recenter-slider-container">
                <input type="range" id="recenterIntervalSlider" min="250" max="2500" step="250" value="1000" oninput="handleRecenterIntervalChange()" aria-label="Intervalo de centralização em milissegundos">
                <span id="recenterIntervalValue" aria-live="polite">1000ms</span>
            </div>
        </div>
        <div class="control-group">
            <label for="voiceSelector">Voz:</label>
            <select id="voiceSelector" aria-label="Selecionar voz" onchange="saveSpeechSettings()"></select>
        </div>
        <div class="control-group">
            <label for="rateSlider">Velocidade:</label>
            <input type="range" id="rateSlider" min="0.5" max="5" step="0.1" value="1" oninput="updateSliderLabels(); saveSpeechSettings();">
            <span id="rateValue" aria-live="polite">1x</span>
        </div>
        <div class="control-group">
            <label for="pitchSlider">Tom:</label>
            <input type="range" id="pitchSlider" min="0" max="2" step="0.1" value="1" oninput="updateSliderLabels(); saveSpeechSettings();">
            <span id="pitchValue" aria-live="polite">1</span>
        </div>
        """ + report_button_html + """
    </div>

    <div id="usage-instructions" role="complementary" aria-labelledby="usage-heading">
        <h2 id="usage-heading">Instruções de Uso</h2>
        <ul>
            <li><strong>Menu de Acessibilidade:</strong> Use o menu flutuante (botão com o ícone de acessibilidade) para personalizar sua experiência. Você pode alterar o tamanho e o tipo da fonte, trocar o tema de cores e ativar a leitura em voz alta do texto.</li>
            <li><strong>Acesso via Celular:</strong> Para garantir que todas as funcionalidades funcionem corretamente, abra este arquivo diretamente em um navegador web (como Chrome, Safari, Firefox), em vez de usar o visualizador interno de aplicativos (como WhatsApp, Gmail, etc).</li>
        """ + report_button_instructions + """
        </ul>
    </div>

    <main id="main-content" role="main">
    """

    return merged_html, report_button_forms