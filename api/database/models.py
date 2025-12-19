from sqlmodel import SQLModel, Field
from datetime import datetime, date
from typing import Optional

class AtoNormativo(SQLModel, table=True):
  id: Optional[int] = Field(default=None, primary_key=True)
  tipo_ato: str
  numero_ato: int
  orgao: str
  data_publicacao: date
  ementa: str
  created_at: datetime = Field(default_factory=datetime.now)
  deleted: bool = Field(default=False)

class ExecucaoLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    data_hora: datetime = Field(default_factory=datetime.now)
    registros_capturados: int
    tempo_execucao_segundos: float
    status: str 
    mensagem_erro: Optional[str] = None

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False)
    hashed_password: str