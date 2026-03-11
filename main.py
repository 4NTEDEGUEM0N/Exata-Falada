import uvicorn
from fastapi import FastAPI
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

from routes.user_routes import user_router
app.include_router(user_router)

@app.get("/")
def health_check():
    return {"status": "online"}

if __name__ == "__main__":
    logger.info("Starting the API")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
    #uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
