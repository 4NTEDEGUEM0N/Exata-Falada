import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.core import settings, upgrade_db

from app.api.routers import (
    user_router,
    converter_router,
    task_router,
    patcher_router,
    library_router
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Application...")
    os.makedirs(settings.LIBRARY_DIR, exist_ok=True)
    if settings.STORAGE_PROVIDER == "local":
        os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    upgrade_db()
    logger.info("Initial setup completed.")
    yield
    logger.info("Closing Application...")

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://exatafalada.duckdns.org",
    "https://exatafalada.tec.br"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)

app.include_router(user_router)
app.include_router(converter_router)
app.include_router(task_router)
app.include_router(patcher_router)
app.include_router(library_router)

@app.get("/")
def health_check():
    return {"status": "online"}

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting the API")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
    #uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
