from sqlmodel import Session, create_engine, select, SQLModel
from services.auth_service import AuthService
from database.models import AtoNormativo, ExecucaoLog, User
from datetime import date, timedelta
from sqlalchemy import text
import os

from dotenv import load_dotenv
from pathlib import Path
raiz_projeto = Path(__file__).resolve().parent.parent.parent
caminho_env = raiz_projeto / ".env"
load_dotenv(dotenv_path=caminho_env)

def seed_db(db_url: str = "postgresql://user:password@localhost:5432/desafio_python"):
    engine = create_engine(db_url, echo=True)
    
    # Cria as tabelas se elas não existirem
    print("[SEED] Garantindo que as tabelas existem...")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Limpa tabelas 
        print("[SEED] Limpando dados antigos...")
        session.execute(text("TRUNCATE TABLE execucaolog, atonormativo, \"user\" RESTART IDENTITY CASCADE"))
        session.commit()

        # Popula AtoNormativo
        print("[SEED] Populando Atos...")
        atos = [
            AtoNormativo(
                tipo_ato="Portaria",
                numero_ato=100 + i,
                orgao="Órgão Exemplo",
                data_publicacao=date.today() - timedelta(days=i),
                ementa=f"Ementa de exemplo {i}",
            ) for i in range(5)
        ]
        session.add_all(atos)

        # Popula ExecucaoLog
        print("[SEED] Populando Logs...")
        logs = [
            ExecucaoLog(
                registros_capturados=10 * (i+1),
                tempo_execucao_segundos=1.5 * (i+1),
                status="SUCESSO" if i % 2 == 0 else "ERRO",
                mensagem_erro=None if i % 2 == 0 else f"Erro {i}"
            ) for i in range(3)
        ]
        session.add_all(logs)
        session.commit()

def seed_admin(db_url: str = "postgresql://user:password@localhost:5432/desafio_python"):
    engine = create_engine(db_url, echo=True)
    with Session(engine) as session:
        username = os.environ.get("ADMIN_USER")
        password = os.environ.get("ADMIN_PASSWORD")
        if not username or not password:
            print("[-] ADMIN_USER ou ADMIN_PASSWORD não configurados no ambiente. Pulando criação do admin.")
            return
        
        # Busca se já existe
        admin = session.exec(select(User).where(User.username == username)).first()
        
        if not admin:
            print(f"[SEED] Criando usuário {username}...")
            service = AuthService(session)
            service.criar_usuario({
                "username": username.strip(),
                "password": password.strip()
            })
            print("[SEED] Admin criado com sucesso!")
        else:
            print("[SEED] Admin já existe. Pulando...")

if __name__ == "__main__":
    # Use a URL do seu ambiente ou a padrão
    URL = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/desafio_python")
    seed_db(URL)
    seed_admin(URL)
    print("\n[OK] Banco populado com sucesso.")