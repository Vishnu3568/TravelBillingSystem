import jwt
import logging
from datetime import datetime, timedelta
import bcrypt
from fastapi import HTTPException, status
from app.config import settings

# Initialize logging
logger = logging.getLogger("security")

# Startup verification of the JWT Secret (matches Java's profile-specific security check)
if settings.JWT_SECRET == "travel-billing-default-secret-key-change-me-please-32chars":
    if not settings.is_dev:
        raise ValueError(
            "CRITICAL SECURITY ERROR: Cannot start application in production ('prod' profile) "
            "with default fallback JWT secret key!"
        )
    else:
        logger.warning("========================================================================")
        logger.warning("  WARNING: USING DEFAULT INSECURE FALLBACK JWT SECRET KEY!")
        logger.warning("  Please configure 'JWT_SECRET' environment variable for production.")
        logger.warning("========================================================================")

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception as e:
        logger.error(f"Password verification failed: {e}")
        return False

def create_access_token(username: str, role: str) -> str:
    # Set expiration
    expiration_seconds = settings.JWT_EXPIRATION_MS / 1000
    expire = datetime.utcnow() + timedelta(seconds=expiration_seconds)
    
    payload = {
        "sub": username,
        "role": role,
        "iat": datetime.utcnow(),
        "exp": expire
    }
    
    encoded_jwt = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# FastAPI Dependencies for Authorization
from fastapi import Depends, Header
from typing import List

def get_current_user(authorization: str = Header(..., description="Bearer JWT Token")) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must start with Bearer"
        )
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    return payload

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = [r.upper() for r in allowed_roles]

    def __call__(self, current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role", "EMPLOYEE").upper()
        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: insufficient permissions"
            )
        return current_user

