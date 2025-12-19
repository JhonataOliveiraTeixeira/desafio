from fastapi import APIRouter, Depends
from sqlmodel import Session
from datetime import date
from typing import Optional, List

from database.config import get_session
from database.models import AtoNormativo, ExecucaoLog
from services.ato_service import AtoService 

router = APIRouter()

@router.get("/atos/", response_model=List[AtoNormativo])
def read_atos(
    data_publicacao: Optional[date] = None,
    search: Optional[str] = None,
    session: Session = Depends(get_session)
):
    
    return AtoService(session).get_atos_filtrados(
        data_publicacao=data_publicacao,
        search=search
    )
@router.get("/atos/{ato_id}", response_model=AtoNormativo)
def get_ato_by_id(ato_id: int, session: Session = Depends(get_session)) -> AtoNormativo:
    ato = AtoService(session).get_ato_by_id(ato_id)
    return ato

@router.get("/dashboard/")
def get_dashboard_data(
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    search: Optional[str] = None, # Novo campo de busca
    session: Session = Depends(get_session)
):
    return AtoService(session).get_dados_dashboard(data_inicio, data_fim, search)


@router.post("/atos/", response_model=AtoNormativo, status_code=201)
def create_ato(ato: AtoNormativo, session: Session = Depends(get_session)):
    return AtoService(session).create_ato(ato)

@router.put("/atos/{ato_id}", response_model=AtoNormativo)
def update_ato(ato_id: int, ato_data: AtoNormativo, session: Session = Depends(get_session)):
    return AtoService(session).update_ato(ato_id, ato_data)

@router.delete("/atos/{ato_id}", status_code=204)
def delete_ato(ato_id: int, session: Session = Depends(get_session)):
    return AtoService(session).delete_ato(ato_id)

