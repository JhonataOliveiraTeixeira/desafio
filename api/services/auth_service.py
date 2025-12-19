from sqlmodel import Session, select
from passlib.context import CryptContext
from fastapi import HTTPException
from jose import jwt
from sqlalchemy import func, text
from datetime import datetime, timedelta
from typing import Optional, Any
import os

from database.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, session: Session):
        self.session = session

    def criar_usuario(self, user_data: dict):
        existing = self.session.exec(
            select(User).where(User.username == user_data["username"])
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username já existe")

        h_password = pwd_context.hash(user_data["password"])
        novo_user = User(username=user_data["username"], hashed_password=h_password)
        self.session.add(novo_user)
        self.session.commit()
        self.session.refresh(novo_user)
        return novo_user

    def authenticate_user(self, username: str, password: str):

        self.session.expire_all()
        stmt = select(User).where(User.username == username.strip())
        user = self.session.exec(stmt).first()

        if not user:
            return None
        if not pwd_context.verify(password, user.hashed_password):
            return None
        return user

    def create_access_token(self, subject: str, expires_seconds: Optional[int] = 3600) -> str:
        secret = os.environ.get("JWT_TOKEN")
        if not secret:
            raise HTTPException(status_code=500, detail="JWT_TOKEN não configurada no ambiente")

        to_encode: dict[str, Any] = {"sub": subject}
        if expires_seconds:
            expire = datetime.utcnow() + timedelta(seconds=expires_seconds)
            to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(to_encode, secret, algorithm="HS256")
        return encoded_jwt