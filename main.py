from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import upgrade_db
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Aplication...")
    upgrade_db()
    logger.info("Initial setup completed.")
    yield
    logger.info("Closing Aplication...")

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
    "https://exatafalada.duckdns.org"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    #allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)

from routes.user_routes import user_router
app.include_router(user_router)
from routes.converter_routes import converter_router
app.include_router(converter_router)
from routes.task_routes import task_router
app.include_router(task_router)
from routes.patcher_routes import patcher_router
app.include_router(patcher_router)

@app.get("/")
def health_check():
    return {"status": "online"}

if __name__ == "__main__":
    import uvicorn
    from config import settings
    
    logger.info("Starting the API")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
    #uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
