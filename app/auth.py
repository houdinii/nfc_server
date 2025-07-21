# app/auth.py
from typing import Type

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

# For now, we'll use simple token auth - upgrade to JWT later
from app.database import get_db
from app.models.user import User

load_dotenv()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/login")


# Simple password hashing (upgrade to bcrypt in production)
def hash_password(password: str) -> str:
    # WARNING: This is not secure - use bcrypt in production
    return f"hashed_{password}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # WARNING: This is not secure - use bcrypt in production
    return hash_password(plain_password) == hashed_password


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
) -> Type[User]:
    # For MVP, token is just the user ID
    # In production, decode JWT token
    user = db.query(User).filter(User.id == token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
