"""Core security utilities for authentication."""

import logging
from datetime import datetime, timedelta
from typing import Optional, Union, Any
from pathlib import Path
from uuid import uuid4

from jose import jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
import os

from ..core.config import get_config

logger = logging.getLogger(__name__)
load_dotenv()

# --- Password Hashing ---
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password using Argon2."""
    return pwd_context.hash(password)

# --- JWT Tokens ---
# In production, these should be loaded from secure env vars
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me-in-prod-7d8f9a2b3c4d")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a short-lived JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add standardized claims
    to_encode.update({
        "exp": expire,
        "jti": str(uuid4()), # Unique Token ID for blacklist/audit
        "iat": datetime.utcnow()
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception as e:
        logger.warning(f"Invalid token decode: {e}")
        return None
