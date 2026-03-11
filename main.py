import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import upgrade_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Aplication...")
    upgrade_db()
    print("Initial setup completed.")
    yield
    print("Closing Aplication...")

app = FastAPI(lifespan=lifespan)

from routes.user_routes import user_router
app.include_router(user_router)

@app.get("/")
def health_check():
    return {"status": "online"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
