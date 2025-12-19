from typing import List
from fastapi import FastAPI, WebSocket
from contextlib import asynccontextmanager
from fastapi.params import Depends
from sqlmodel import SQLModel, create_engine
from router.logs_router import logs_router
from router.ato_router import router 
from router.auth_router import auth_router
from router.redirects_router import router_redirect
from services.guard import get_current_user
import os
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")


DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL não está configurada no ambiente.")


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()


engine = create_engine(DATABASE_URL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    SQLModel.metadata.create_all(engine)
    yield

app = FastAPI(
    title="API RF - Service Layer",
    version="1.0.0",
    lifespan=lifespan,
    port=8000
)

app.include_router(router, tags=["Atos Normativos"], dependencies=[Depends(get_current_user)])
app.include_router(router_redirect)
app.include_router(logs_router, tags=["Logs"], dependencies=[Depends(get_current_user)])
app.include_router(auth_router, tags=["Autenticação"] )



