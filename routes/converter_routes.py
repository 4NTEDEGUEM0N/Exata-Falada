from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from fastapi.responses import FileResponse
from config import settings
import os
import shutil
import fitz
import time
import google.generativeai as genai
from PIL import Image
from prompt_html import get_prompt, get_html
import re
import base64
import html
from typing import List, Dict, Optional, Tuple, Any
from models.user_model import UserModel
from models.task_model import TaskModel
from database import get_db
from .user_routes import get_current_user
from sqlalchemy.orm import Session
from enum import Enum

import logging

logger = logging.getLogger(__name__)

converter_router = APIRouter(prefix="/converter", tags=["converter"])

class TaskStatusEnum(str, Enum):
    CREATED = "Created"
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    ERROR = "Error"

@converter_router.post("/")
async def convert_pdf(paginas: str = "", file: UploadFile = File(...), db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O arquivo deve ser um PDF.")
    
    if file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail="Arquivo muito grande. O limite é 50MB.")

    pdf_filename = re.sub(r'[^a-zA-Z0-9.\-_]', '_', file.filename)
    task_data = {"pdf_filename": pdf_filename, "status": TaskStatusEnum.CREATED, "user_id": current_user.id}
    new_task = TaskModel(**task_data)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    unique_filename = f"{new_task.id}_{pdf_filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        new_task.status = TaskStatusEnum.PROCESSING
        db.commit()

        html_output_path = processar_pdf(file_path, paginas)
        html_filename = os.path.basename(html_output_path)

        new_task.status = TaskStatusEnum.COMPLETED
        new_task.html_filename = html_filename
        db.commit()

        return {
            "pdf_filename": pdf_filename,
            "html_filename": html_filename,
            "status": "success"
        }
    
    except ValueError as ve:
        new_task.status = TaskStatusEnum.ERROR
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
        
    except FileNotFoundError:
        new_task.status = TaskStatusEnum.ERROR
        db.commit()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arquivo não encontrado durante o processamento.")
        
    except Exception as e:
        new_task.status = TaskStatusEnum.ERROR
        db.commit()
        logger.critical(f"ERRO CRÍTICO: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ocorreu um erro inesperado ao processar o arquivo.")

@converter_router.get("/download/{filename}")
async def baixar_arquivo(filename: str, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    filename = os.path.basename(filename)
    task = db.query(TaskModel).filter(TaskModel.html_filename == filename).first()
    if not task:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado ou já expirou.")
    
    if task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED")

    file_path = os.path.join(settings.OUTPUT_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado ou já expirou.")
        
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )


def parse_paginas(string_paginas: str, total_paginas: int) -> Optional[List[int]]:
    if not string_paginas.strip():
        return list(range(total_paginas))
    
    paginas = set()
    partes = string_paginas.strip().replace(" ", "").split(',')
    for parte in partes:
        parte = parte.strip()
        if not parte: continue
        if '-' in parte:
            inicio, fim = parte.split('-', 1)
            try:
                start_idx = int(inicio) - 1
                if not fim:
                    end_idx = total_paginas - 1
                else:
                    end_idx = int(fim) - 1
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

def pdf_para_imagens(caminho_pdf: str, paginas_selecionadas: List[int], dpi: int = 100) -> Tuple[str, List[str]]:
    pdf_basename = os.path.basename(caminho_pdf)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    pasta_saida = os.path.join('files/temp_processing', f"{pdf_basename}_{timestamp}")
    os.makedirs(pasta_saida, exist_ok=True)
    image_paths = []

    try:
        with fitz.open(caminho_pdf) as documento:
            for numero_pagina in paginas_selecionadas:
                pagina = documento.load_page(numero_pagina)
                imagem = pagina.get_pixmap(dpi=dpi)
                
                nome_arquivo = os.path.join(pasta_saida, f"pagina_{numero_pagina + 1}.png")
                imagem.save(nome_arquivo)
                
                image_paths.append(nome_arquivo)
                logger.info(f"Página {numero_pagina + 1} salva como {nome_arquivo}")
    except Exception as e:
        logger.error(f"Erro ao converter PDF para imagens: {e}", exc_info=True)
        raise RuntimeError(f"Erro na conversão PDF para imagem: {e}")

    return pasta_saida, image_paths

def analisar_imagens_com_gemini(pdf_basename: str, lista_caminhos: List[str]) -> List[Dict[str, Any]]:
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    modelo = genai.GenerativeModel('gemini-2.5-flash-lite')
    respostas = []

    for caminho in lista_caminhos:
        try:
            logger.info(f"Processando: {caminho}...")
            
            if not os.path.exists(caminho):
                raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
                
            imagem = Image.open(caminho)

            with open(caminho, "rb") as image_file:
                image_data = image_file.read()

            match_pagina = re.search(r"pagina_(\d+)\.png$", caminho)
            current_page_num_in_doc = match_pagina.group(1) if match_pagina else "Desconhecida"
            
            base64_image_data = base64.b64encode(image_data).decode('utf-8')
            prompt = get_prompt(pdf_basename, imagem.size, current_page_num_in_doc)
            
            response = modelo.generate_content([prompt, imagem])
            imagem.close()

            final_finish_reason = 'UNKNOWN'
            html_body = None
            
            if response and hasattr(response, 'candidates') and response.candidates:
                final_finish_reason = response.candidates[0].finish_reason.value if response.candidates[0].finish_reason else 'UNKNOWN'

                response_text_content = response.text
                if not response_text_content and response.candidates[0].content and response.candidates[0].content.parts:
                    response_text_content = ''.join(
                        part.text for part in response.candidates[0].content.parts if hasattr(part, 'text')
                    )

                if response_text_content:
                    match = re.search(r"```html\s*(.*?)\s*```", response_text_content, re.DOTALL | re.IGNORECASE)
                    if match:
                        html_body = match.group(1).strip()
                    else:
                        trimmed_text = response_text_content.strip()
                        if trimmed_text.startswith("<") and trimmed_text.endswith(">") and \
                            re.search(r"<p|<div|<span|<table|<ul|<ol|<h[1-6]", trimmed_text, re.IGNORECASE):
                            html_body = trimmed_text
                            
                    if html_body:
                        html_body = re.sub(r'<bdi>([a-zA-Z0-9_](?:<sup>.*?</sup>)?)</bdi>', r'\1', html_body)
                        html_body = re.sub(r'<bdi>(\\[a-zA-Z]+(?:\{.*?\})?(?:\s*\^\{.*?\})?(?:\s*_\{.*?\})?)</bdi>', r'\1',
                                            html_body)
                        html_body = re.sub(r'<bdi>\s*</bdi>', '', html_body)

            if html_body is None:
                logger.warning(f"Aviso: Falha ao extrair HTML para {pdf_basename} (pág {current_page_num_in_doc}).")
                if response:
                    logger.warning(f"Texto bruto (300c): {str(response.text)[:300]}...")
                    try:
                        logger.warning(f"Motivo: {final_finish_reason} ({response.candidates[0].finish_reason.name})")
                    except AttributeError:
                        logger.warning(f"Motivo: {final_finish_reason}")
            
            resposta = {
                "page_num_in_doc": current_page_num_in_doc, 
                "body": html_body, 
                "base64_image": base64_image_data,
                "status": "success"
            }
            respostas.append(resposta)
            logger.info("✅ Sucesso!")
            
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar {caminho}: {e}", exc_info=True)
            if 'imagem' in locals() and hasattr(imagem, 'close'):
                imagem.close()
                
            match_pagina = re.search(r"pagina_(\d+)\.png$", caminho)
            current_page_num = match_pagina.group(1) if match_pagina else "Desconhecida"
            respostas.append({
                "page_num_in_doc": current_page_num,
                "body": None,
                "base64_image": None,
                "status": "error",
                "error_msg": str(e)
            })
            
    return respostas

def merge_html(pdf_filename_title: str, report_button: bool, content_list: List[Dict[str, Any]]):
    merged_html, report_button_forms = get_html(pdf_filename_title, report_button)

    for i, content_data in enumerate(content_list):
        page_num_in_doc = content_data.get("page_num_in_doc", "Desconhecida")
        html_body = content_data.get("body")
        base64_image = content_data.get("base64_image")
        status = content_data.get("status", "success")
        error_msg = content_data.get("error_msg", "")
        
        if i > 0: 
            merged_html += f"\n<hr class=\"page-separator\" aria-hidden=\"true\">\n"
            
        merged_html += f"<article class='page-content' id='page-{page_num_in_doc}' aria-labelledby='page-heading-{page_num_in_doc}'>\n"
        merged_html += f"<h2 id='page-heading-{page_num_in_doc}'>Página {page_num_in_doc}</h2>\n"
        
        if html_body:
            merged_html += html_body
        elif status == "error":
            merged_html += f"<p><i>[Erro ao processar a página {page_num_in_doc}: {html.escape(error_msg)}]</i></p>"
        else:
            merged_html += f"<p><i>[Conteúdo não pôde ser extraído para a página {page_num_in_doc}.]</i></p>"
            
        if html_body and base64_image and "[Descrição da imagem:" in html_body:
            safe_alt_text = html.escape(f"Imagem original da página {page_num_in_doc}")
            merged_html += f"""
                <details class="original-page-viewer">
                    <summary>Ver Imagem da Página Original {page_num_in_doc}</summary>
                    <div style="text-align: center; padding: 10px;">
                        <img src="data:image/png;base64,{base64_image}" alt="{safe_alt_text}" style="max-width: 100%; height: auto;" aria-hidden="true">
                    </div>
                </details>
            """
        merged_html += "\n</article>\n"
        
    merged_html += f"\n    </main> \n    {report_button_forms}\n</body>\n</html>"

    output_path = settings.OUTPUT_DIR
    os.makedirs(output_path, exist_ok=True)
    nome_sem_extensao = os.path.splitext(pdf_filename_title)[0]
    full_output_path = os.path.join(output_path, f"{nome_sem_extensao}.html")
    
    with open(full_output_path, "w", encoding="utf-8") as f: 
        f.write(merged_html)
        
    logger.info(f"HTML salvo com sucesso em: {full_output_path}")
    return full_output_path

def processar_pdf(caminho_pdf: str, string_paginas: str):
    if not os.path.exists(caminho_pdf):
        raise FileNotFoundError(f"Erro: Arquivo PDF não encontrado em {caminho_pdf}")

    try:
        with fitz.open(caminho_pdf) as temp_doc:
            total_paginas = temp_doc.page_count
    except Exception as e:
        raise ValueError(f"Erro ao abrir o PDF {caminho_pdf}: {e}")
    
    logger.info("Iniciando o Parser das Páginas")
    paginas_selecionadas = parse_paginas(string_paginas, total_paginas)
    if paginas_selecionadas is None:
        raise ValueError("Falha no parser de páginas. Verifique o formato inserido.")
    logger.info(f"Páginas a processar: {[p + 1 for p in paginas_selecionadas]}")
    logger.info("Fim do Parse das Páginas\n")

    logger.info("Convertendo o PDF para imagens...")
    pasta_saida, image_paths = pdf_para_imagens(caminho_pdf, paginas_selecionadas)
    
    if not image_paths: 
        if os.path.exists(pasta_saida):
            shutil.rmtree(pasta_saida, ignore_errors=True)
        raise RuntimeError("Falha ao converter PDF para imagens ou nenhuma imagem gerada.")
        
    logger.info("Fim da conversão\n")

    logger.info("Gerando HTML de cada imagem...")
    pdf_basename = os.path.basename(caminho_pdf)
    respostas = analisar_imagens_com_gemini(pdf_basename, image_paths)
    logger.info("Os HTML foram gerados\n")

    logger.info("Mesclando os HTML...")
    html_output_path = merge_html(pdf_basename, True, respostas)
    logger.info("HTML Mesclado\n")
    
    logger.info("Limpando arquivos temporários...")
    try:
        shutil.rmtree(pasta_saida)
        logger.info("Arquivos temporários removidos com sucesso.")
    except Exception as e:
        logger.warning(f"Aviso: Não foi possível remover a pasta temporária {pasta_saida}: {e}")
    
    return html_output_path
