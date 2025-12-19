import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select

from database.config import get_session
from database.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    session: Session = Depends(get_session)
) -> User:
    """
    Dependency Guard que valida o JWT e retorna o usuário do banco.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    secret = os.environ.get("JWT_TOKEN")
    if not secret:
        raise HTTPException(status_code=500, detail="JWT_TOKEN não configurada")

    try:
        # 1. Decodifica o Token
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        username: str = payload.get("sub") or ""
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # 2. Busca o usuário no banco (usando sua Session injetada)
    user = session.exec(select(User).where(User.username == username)).first()
    
    if user is None:
        raise credentials_exception
        
    return user