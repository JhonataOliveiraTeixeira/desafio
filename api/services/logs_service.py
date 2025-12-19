from datetime import date
from typing import Optional
from sqlmodel import Session
from sqlmodel import Session, select


from database.models import AtoNormativo, ExecucaoLog


class LogsService:
    def __init__(self, session: Session):
      self.session = session

    def create_log(self, log: ExecucaoLog):
        self.session.add(log)
        self.session.commit()
        self.session.refresh(log)
        return log
    
    def get_dashboard_data(
        self,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None
    ):

        query = select(AtoNormativo).where(AtoNormativo.deleted == False)

        if data_inicio:
            query = query.where(AtoNormativo.data_publicacao >= data_inicio)
        if data_fim:
            query = query.where(AtoNormativo.data_publicacao <= data_fim)

        atos = self.session.exec(query).all()
        
        total_atos = len(atos)

        por_orgao = {}
        for ato in atos:
            por_orgao[ato.orgao] = por_orgao.get(ato.orgao, 0) + 1

        por_tipo = {}
        for ato in atos:
            por_tipo[ato.tipo_ato] = por_tipo.get(ato.tipo_ato, 0) + 1

        return {
            "periodo": {"inicio": data_inicio, "fim": data_fim},
            "total_registros": total_atos,
            "distribuicao_por_orgao": por_orgao,
            "distribuicao_por_tipo": por_tipo
        }