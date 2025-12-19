from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import  OAuth2PasswordRequestForm
from sqlmodel import Session

from database.config import get_session
from services.auth_service import AuthService

auth_router = APIRouter()


@auth_router.post("/usuarios/", tags=["Autenticação"])
def criar_usuario(user_data: dict, session: Session = Depends(get_session)):
    return AuthService(session).criar_usuario(user_data)


@auth_router.post("/token", tags=["Autenticação"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    service = AuthService(session)
    user = service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
        )
    token = service.create_access_token(user.username)
    return {"access_token": token, "token_type": "bearer"}
