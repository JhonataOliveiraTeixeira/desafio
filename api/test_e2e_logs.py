import os
from datetime import datetime, timedelta
import pytest
from httpx import AsyncClient, ASGITransport

# Aponta para o banco de testes antes de importar a aplicação
os.environ.setdefault("DATABASE_URL", "postgresql://user:password@localhost:5432/desafio_python_teste")
from api.main import app
from sqlmodel import SQLModel, create_engine, Session, delete
from database.models import ExecucaoLog

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/desafio_python_teste")
engine = create_engine(DATABASE_URL)
BASE_URL = os.environ.get("API_URL", "http://localhost:8000")

@pytest.fixture(scope="function", autouse=True)
def prepara_banco():
    # Garante que as tabelas existam e limpa antes de cada teste
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        session.exec(delete(ExecucaoLog))
        session.commit()
        # Insere um log inicial
        session.add(ExecucaoLog(registros_capturados=5, tempo_execucao_segundos=0.5, status="SUCESSO", mensagem_erro=None))
        session.commit()
    yield
    # Limpa após
    with Session(engine) as session:
        session.exec(delete(ExecucaoLog))
        session.commit()

@pytest.mark.asyncio
async def test_criar_log():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        payload = {
            "registros_capturados": 12,
            "tempo_execucao_segundos": 2.3,
            "status": "SUCESSO",
            "mensagem_erro": None
        }
        response = await ac.post("/logs/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["registros_capturados"] == 12
        assert data["status"] == "SUCESSO"

@pytest.mark.asyncio
async def test_dashboard_logs():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        # Insere mais alguns logs para testar agregação
        now = datetime.now()
        payloads = [
            {"registros_capturados": 3, "tempo_execucao_segundos": 1.0, "status": "SUCESSO", "mensagem_erro": None},
            {"registros_capturados": 7, "tempo_execucao_segundos": 2.0, "status": "ERRO", "mensagem_erro": "Falha de exemplo"}
        ]
        for p in payloads:
            await ac.post("/logs/", json=p)

        # Chama o endpoint de dashboard sem filtros
        response = await ac.get("/logs/dashboard/")
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

        # Chama o endpoint com intervalo de datas
        inicio = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        fim = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        response2 = await ac.get(f"/logs/dashboard/?data_inicio={inicio}&data_fim={fim}")
        assert response2.status_code == 200
        assert isinstance(response2.json(), dict)
