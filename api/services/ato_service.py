from fastapi import HTTPException
from fastapi.params import Depends
from sqlmodel import Session, select, func, and_
from sqlalchemy.sql import func
from datetime import date
from typing import Any, List, Optional

from database.config import get_session
from database.models import AtoNormativo, ExecucaoLog



class AtoService:
    def __init__(self, session: Session):
        self.session = session

    def get_atos_filtrados(self, data_publicacao: Optional[date], search: Optional[str]):
        """Lógica de filtragem e busca."""
        query = select(AtoNormativo).where(AtoNormativo.deleted == False)

        if data_publicacao:
            query = query.where(AtoNormativo.data_publicacao == data_publicacao)

        if search:
            query = query.where(
                (func.lower(AtoNormativo.ementa).ilike(f"%{search}%")) | 
                (func.lower(AtoNormativo.numero_ato).ilike(f"%{search}%"))
            )
        
        # O Service executa a query e retorna o resultado
        return self.session.exec(query).all()
    
    def get_ato_by_id(self, ato_id: int):
        ato = self.session.get(AtoNormativo, ato_id)
        if not ato or ato.deleted:
            raise HTTPException(status_code=404, detail="Ato Normativo não encontrado")
        return ato

    def get_dados_dashboard(self, data_inicio: Optional[date], data_fim: Optional[date], search: Optional[str] = None):
    # Base da query com exclusão lógica
        base_where : List[Any] = [AtoNormativo.deleted == False]
        
        if data_inicio:
            base_where.append(AtoNormativo.data_publicacao >= data_inicio)
        if data_fim:
            base_where.append(AtoNormativo.data_publicacao <= data_fim)
        if search:
            # Campo de busca (Search) na ementa ou órgão
            base_where.append(func.lower(AtoNormativo.ementa).ilike(f"%{search}%"))

        # 1. Total Geral
        total = self.session.exec(
            select(func.count()).where(and_(*base_where))
        ).one()

        # 2. Distribuição por Órgão (Agregado no Banco)
        # Resultado esperado: [("Órgão A", 10), ("Órgão B", 5)]
        query_orgao = self.session.exec(
            select(AtoNormativo.orgao, func.count())
            .where(and_(*base_where))
            .group_by(AtoNormativo.orgao)
        ).all()

        # 3. Distribuição por Tipo
        query_tipo = self.session.exec(
            select(AtoNormativo.tipo_ato, func.count())
            .where(and_(*base_where))
            .group_by(AtoNormativo.tipo_ato)
        ).all()

        return {
            "total_registros": total,
            "distribuicao_por_orgao": {row[0]: row[1] for row in query_orgao},
            "distribuicao_por_tipo": {row[0]: row[1] for row in query_tipo},
        }
    def create_ato(self, ato: AtoNormativo ):
        self.session.add(ato)
        self.session.commit()
        self.session.refresh(ato)
        return ato

    def update_ato(self, ato_id: int, ato_data: AtoNormativo):
        ato_db = self.session.get(AtoNormativo, ato_id)
        if not ato_db or ato_db.deleted:
            return HTTPException(status_code=404, detail="Ato normativo não encontrado")

        ato_dados = ato_data.model_dump(exclude_unset=True, exclude={"id", "created_at", "deleted"})
        for key, value in ato_dados.items():
            setattr(ato_db, key, value)

        self.session.add(ato_db)
        self.session.commit()
        self.session.refresh(ato_db)
        return ato_db

    def delete_ato(self, ato_id: int):
        ato_db = self.session.get(AtoNormativo, ato_id)
        if not ato_db:
            raise HTTPException(status_code=404, detail="Ato não encontrado")
        
        ato_db.deleted = True
        self.session.add(ato_db)
        self.session.commit()
        return {"message": "Ato excluído com sucesso"}

    