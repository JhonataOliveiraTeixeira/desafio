from datetime import datetime
import os
import pytest
from httpx import AsyncClient, ASGITransport

# Configura variáveis de ambiente para o ambiente de teste

os.environ["mode"] = "development"
os.environ["DATABASE_URL"] = "postgresql://user:password@localhost:5432/desafio_python_teste"

from api.main import app
from sqlmodel import SQLModel, create_engine, Session, delete
from database.models import AtoNormativo

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/desafio_python_teste")
engine = create_engine(DATABASE_URL)

BASE_URL = os.environ.get("API_URL", "http://localhost:8000")

@pytest.fixture(scope="function", autouse=True)
def prepara_banco():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        session.exec(delete(AtoNormativo))
        session.commit()
        session.add(AtoNormativo(tipo_ato="Portaria", numero_ato=1, orgao="Órgão Teste", data_publicacao=datetime.strptime("2023-01-01", "%Y-%m-%d").date(), ementa="Ementa teste"))
        session.commit()
    yield
    with Session(engine) as session:
        session.exec(delete(AtoNormativo))
        session.commit()

@pytest.mark.asyncio
async def test_criar_ato():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.post("/atos/", json={
            "tipo_ato": "Resolução",
            "numero_ato": 2,
            "orgao": "Órgão Teste",
            "data_publicacao": "2023-01-02",
            "ementa": "Ementa de resolução"
        })
        assert response.status_code == 201
        assert response.json()["tipo_ato"] == "Resolução"

@pytest.mark.asyncio
async def test_listar_atos():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.get("/atos/")
        assert response.status_code == 200
        assert any(ato["tipo_ato"] == "Portaria" for ato in response.json())

@pytest.mark.asyncio
async def test_buscar_ato_por_id():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        resp = await ac.post("/atos/", json={
            "tipo_ato": "Instrução",
            "numero_ato": 3,
            "orgao": "Órgão Teste",
            "data_publicacao": "2023-01-03",
            "ementa": "Ementa instrução"
        })
        ato_id = resp.json()["id"]
        response = await ac.get(f"/atos/{ato_id}")
        assert response.status_code == 200
        assert response.json()["tipo_ato"] == "Instrução"

@pytest.mark.asyncio
async def test_atualizar_ato():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
       #  Cria um novo ato
        resp = await ac.post("/atos/", json={
            "tipo_ato": "Deliberação",
            "numero_ato": 4,
            "orgao": "Órgão Teste",
            "data_publicacao": "2023-01-04",
            "ementa": "Ementa deliberação"
        })
        ato_id = resp.json()["id"]
        # Atualiza
        response = await ac.put(f"/atos/{ato_id}", json={
            "tipo_ato": "Deliberação Atualizada",
            "numero_ato": 4,
            "orgao": "Órgão Teste",
            "data_publicacao": "2023-01-04",
            "ementa": "Ementa atualizada"
        })
        assert response.status_code == 200
        assert response.json()["tipo_ato"] == "Deliberação Atualizada"

@pytest.mark.asyncio
async def test_deletar_ato():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        # Cria um novo ato
        resp = await ac.post("/atos/", json={
            "tipo_ato": "Aviso",
            "numero_ato": 5,
            "orgao": "Órgão Teste",
            "data_publicacao": "2023-01-05",
            "ementa": "Ementa aviso"
        })
        ato_id = resp.json()["id"]
        # Deleta
        response = await ac.delete(f"/atos/{ato_id}")
        assert response.status_code == 204
        # Confirma remoção
        response = await ac.get(f"/atos/{ato_id}")
        assert response.status_code == 404
