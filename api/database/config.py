import os
from sqlmodel import create_engine, Session

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    mode = os.environ.get("mode", "development") 
    if mode == "production" or mode == "development":
        DATABASE_URL = "postgresql://user:password@localhost:5432/desafio_python"
    else:
        DATABASE_URL = "postgresql://user:password@localhost:5432/desafio_python_teste"

engine = create_engine(DATABASE_URL)

def get_session():
    with Session(engine) as session:
        yield session