from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends
from sqlmodel import Session

from services.logs_service import LogsService

from database.config import get_session
from database.models import ExecucaoLog


logs_router = APIRouter()

@logs_router.post("/logs/", response_model=ExecucaoLog, status_code=201)
def create_log(log: ExecucaoLog, session: Session = Depends(get_session)):
  return LogsService(session).create_log(log)

@logs_router.get("/logs/dashboard/")
def get_dashboard_data(
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    session: Session = Depends(get_session)
):
    return LogsService(session).get_dashboard_data(
        data_inicio=data_inicio,
        data_fim=data_fim
    )