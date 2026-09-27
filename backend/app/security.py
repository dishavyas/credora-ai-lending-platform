import os
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .database import get_db
from .models import User

SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
ALGO = "HS256"
MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "480"))
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def hash_password(v): return pwd.hash(v)
def verify_password(raw, hashed): return pwd.verify(raw, hashed)

def token_for(user: User):
    return jwt.encode({"sub": str(user.id), "email": user.email, "role": user.role,
                       "exp": datetime.now(timezone.utc)+timedelta(minutes=MINUTES)}, SECRET, algorithm=ALGO)

def current_user(token: str = Depends(oauth2), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGO])
        user = db.get(User, int(payload["sub"]))
    except (JWTError, KeyError, ValueError):
        user = None
    if not user:
        raise HTTPException(401, "Invalid or expired token")
    return user
