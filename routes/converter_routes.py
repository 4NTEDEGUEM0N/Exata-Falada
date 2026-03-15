from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request, BackgroundTasks, Form
from fastapi.responses import FileResponse
from config import settings
import os
import shutil
import fitz
import time
from google import genai 
from google.genai import types
from PIL import Image
from prompt_html import get_prompt, get_html
import re
import base64
import html
from typing import List, Dict, Optional, Tuple, Any
from models.user_model import UserModel
from models.task_model import TaskModel
from database import get_db, SessionLocal
from .user_routes import get_current_user
from sqlalchemy.orm import Session
from enum import Enum
from pydantic import BaseModel

import logging

logger = logging.getLogger(__name__)

converter_router = APIRouter(prefix="/converter", tags=["converter"])

class TaskStatusEnum(str, Enum):
    CREATED = "Created"
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    COMPLETED_WITH_ERRORS = "Completed with errors"
    ERROR = "Error"

class ConverterRequest(BaseModel):
    paginas: Optional[str] = ""
    dpi: Optional[int] = settings.DEFAULT_DPI
    gemini_workers: Optional[int] = settings.DEFAULT_GEMINI_WORKERS
    gemini_model: Optional[str] = settings.DEFAULT_MODEL
    report_button: Optional[bool] = settings.DEFAULT_REPORT_BUTTON

@converter_router.get("/models")
async def get_models(current_user: UserModel = Depends(get_current_user)):
    return {"available_models": settings.MODELS_LIST, "default_model": settings.DEFAULT_MODEL}

@converter_router.post("/")
async def convert_pdf(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...), 
    paginas: Optional[str] = Form(""),
    dpi: Optional[int] = Form(settings.DEFAULT_DPI),
    gemini_workers: Optional[int] = Form(settings.DEFAULT_GEMINI_WORKERS),
    gemini_model: Optional[str] = Form(settings.DEFAULT_MODEL),
    report_button: Optional[bool] = Form(settings.DEFAULT_REPORT_BUTTON),
    db: Session = Depends(get_db), 
    current_user: UserModel = Depends(get_current_user)
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O arquivo deve ser um PDF.")
    
    if file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail="Arquivo muito grande. O limite é 50MB.")

    if not current_user.admin:
        dpi = settings.DEFAULT_DPI
        gemini_workers = settings.DEFAULT_GEMINI_WORKERS
        gemini_model = settings.DEFAULT_MODEL
        report_button = settings.DEFAULT_REPORT_BUTTON

    converter_request_schema = ConverterRequest(
        paginas=paginas,
        dpi=dpi,
        gemini_workers=gemini_workers,
        gemini_model=gemini_model,
        report_button=report_button
    )

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

        background_tasks.add_task(task_processar_pdf_background, new_task.id, file_path, converter_request_schema)

        return {
            "task_id": new_task.id,
            "message": "Conversão iniciada com sucesso. Acompanhe o progresso."
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


def log_to_task(db_session: Session, task_id: int, message: str, increment_progress: int = 0):
    task = db_session.query(TaskModel).filter_by(id=task_id).first()
    if task:
        timestamp = time.strftime("[%H:%M:%S]")
        new_log = f"{timestamp} {message}\n"
        task.logs = (task.logs or "") + new_log
        if increment_progress > 0:
            task.progress = min(100, (task.progress or 0) + increment_progress)
        db_session.commit()

def task_processar_pdf_background(task_id: int, file_path: str, converter_request_schema: ConverterRequest):
    db: Session = SessionLocal()
    import threading
    db_lock = threading.Lock()
    try:
        task = db.query(TaskModel).filter_by(id=task_id).first()
        if task:
            task.status = TaskStatusEnum.PROCESSING
            db.commit()

        def log_cb(msg, inc=0):
            with db_lock:
                thread_db = SessionLocal()
                try:
                    log_to_task(thread_db, task_id, msg, increment_progress=inc)
                finally:
                    thread_db.close()
        
        log_cb("Iniciando processo de conversão do PDF...", 5)
        html_output_path, tem_erros = processar_pdf(file_path, converter_request_schema, log_cb)
        html_filename = os.path.basename(html_output_path)
        
        task = db.query(TaskModel).filter_by(id=task_id).first()
        if task:
            task.status = TaskStatusEnum.COMPLETED_WITH_ERRORS if tem_erros else TaskStatusEnum.COMPLETED
            task.progress = 100
            task.html_filename = html_filename
            db.commit()
            
        if tem_erros:
            log_cb("Finalizado com alguns erros! HTML parcialmente pronto para download.", 0)
        else:
            log_cb("Finalizado com sucesso! HTML pronto para download.", 0)
    except Exception as e:
        task = db.query(TaskModel).filter_by(id=task_id).first()
        if task:
            task.status = TaskStatusEnum.ERROR
            db.commit()
        log_to_task(db, task_id, f"ERRO CRÍTICO: {e}")
    finally:
        db.close()


@converter_router.get("/status/{task_id}")
async def check_task_status(task_id: int, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    
    if not task:
         raise HTTPException(status_code=404, detail="Tarefa não encontrada")
         
    if task.user_id != current_user.id and not current_user.admin:
         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Acesso negado")
         
    return {
        "status": task.status,
        "progress": task.progress,
        "logs": task.logs,
        "html_filename": task.html_filename
    }


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

def pdf_para_imagens(caminho_pdf: str, paginas_selecionadas: List[int], dpi, log_cb) -> Tuple[str, List[str]]:
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
                log_cb(f"Página {numero_pagina + 1} extraída.", 0)
    except Exception as e:
        logger.error(f"Erro ao converter PDF para imagens: {e}", exc_info=True)
        raise RuntimeError(f"Erro na conversão PDF para imagem: {e}")

    return pasta_saida, image_paths

def processar_imagem(caminho: str, pdf_basename: str, client: genai.Client, gemini_model: str, inc_per_page: int, log_cb):
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
        
        MAX_RETRIES = settings.MAX_RETRIES
        response = None
        
        for attempt in range(MAX_RETRIES):
            try:
                response = client.models.generate_content(
                    model=gemini_model, 
                    contents=[prompt, imagem]
                )
                break
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    wait_time = 2 ** attempt * 5
                    logger.warning(f"Erro na API (tentativa {attempt + 1} de {MAX_RETRIES}) para pág. {current_page_num_in_doc}: {e}. Aguardando {wait_time}s...")
                    log_cb(f"⚠️ Erro na pág {current_page_num_in_doc} (tentativa {attempt + 1}/{MAX_RETRIES}): aguardando {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise e

        imagem.close()

        final_finish_reason = 'UNKNOWN'
        html_body = None
        
        if response and response.candidates:
            candidate = response.candidates[0]
            final_finish_reason = candidate.finish_reason.name if candidate.finish_reason else 'UNKNOWN'

            response_text_content = response.text
            if not response_text_content and candidate.content and candidate.content.parts:
                response_text_content = ''.join(
                    part.text for part in candidate.content.parts if hasattr(part, 'text') and part.text
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
            log_cb(f"Aviso: Falha ao extrair HTML para {pdf_basename} (pág {current_page_num_in_doc}).")
            if response:
                logger.warning(f"Texto bruto (300c): {str(response.text)[:300]}...")
                try:
                    logger.warning(f"Motivo: {final_finish_reason} ({response.candidates[0].finish_reason.name})")
                    log_cb(f"Motivo: {final_finish_reason} ({response.candidates[0].finish_reason.name})")
                except AttributeError:
                    logger.warning(f"Motivo: {final_finish_reason}")
                    log_cb(f"Motivo: {final_finish_reason}")
        
        resposta = {
            "page_num_in_doc": current_page_num_in_doc, 
            "body": html_body, 
            "base64_image": base64_image_data,
            "status": "success" if html_body else "error"
        }
        if html_body is None:
            resposta["error_msg"] = "HTML não pôde ser extraído da resposta do modelo."

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

def analisar_imagens_com_gemini(pdf_basename: str, lista_caminhos: List[str], gemini_model: str, gemini_workers: int, log_cb) -> List[Dict[str, Any]]:
    import concurrent.futures
    from functools import partial
    client = genai.Client(api_key=settings.GOOGLE_API_KEY)
    total_imgs = len(lista_caminhos)
    inc_per_page = max(1, 65 // total_imgs) if total_imgs > 0 else 0

    logger.info(f"Modelo selecionado: {gemini_model}")
    log_cb(f"Modelo selecionado: {gemini_model}", 0)

    func_processar = partial(
        processar_imagem, 
        pdf_basename=pdf_basename, 
        client=client, 
        gemini_model=gemini_model, 
        inc_per_page=inc_per_page, 
        log_cb=log_cb
    )
            
    respostas = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=gemini_workers) as executor:
        results = executor.map(func_processar, lista_caminhos)
        respostas = list(results)
        
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

def processar_pdf(caminho_pdf: str, converter_request_schema: ConverterRequest, log_cb):
    if not os.path.exists(caminho_pdf):
        raise FileNotFoundError(f"Erro: Arquivo PDF não encontrado em {caminho_pdf}")

    try:
        with fitz.open(caminho_pdf) as temp_doc:
            total_paginas = temp_doc.page_count
    except Exception as e:
        raise ValueError(f"Erro ao abrir o PDF {caminho_pdf}: {e}")
    
    log_cb("Iniciando o Parser das Páginas", 5)
    paginas_selecionadas = parse_paginas(converter_request_schema.paginas, total_paginas)
    if paginas_selecionadas is None:
        raise ValueError("Falha no parser de páginas. Verifique o formato inserido.")
    log_cb(f"Páginas a processar: {[p + 1 for p in paginas_selecionadas]}")
    log_cb("Fim do Parse das Páginas\n")

    log_cb("Convertendo o PDF para imagens...", 10)
    pasta_saida, image_paths = pdf_para_imagens(caminho_pdf, paginas_selecionadas, converter_request_schema.dpi, log_cb)
    
    if not image_paths: 
        if os.path.exists(pasta_saida):
            shutil.rmtree(pasta_saida, ignore_errors=True)
        raise RuntimeError("Falha ao converter PDF para imagens ou nenhuma imagem gerada.")
        
    log_cb("Fim da conversão\n")

    log_cb("Gerando HTML de cada imagem...")
    pdf_basename = os.path.basename(caminho_pdf)
    respostas = analisar_imagens_com_gemini(pdf_basename, image_paths, converter_request_schema.gemini_model, converter_request_schema.gemini_workers, log_cb)
    log_cb("Os HTML foram gerados\n")

    log_cb("Mesclando os HTML...", 5)
    html_output_path = merge_html(pdf_basename, converter_request_schema.report_button, respostas)
    log_cb("HTML Mesclado\n", 5)
    
    log_cb("Limpando arquivos temporários...")
    try:
        shutil.rmtree(pasta_saida)
        log_cb("Arquivos temporários removidos com sucesso.")
    except Exception as e:
        logger.warning(f"Aviso: Não foi possível remover a pasta temporária {pasta_saida}: {e}")
    
    tem_erros = any(r.get("status") == "error" or r.get("body") is None for r in respostas)
    return html_output_path, tem_erros

