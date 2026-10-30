"""
backend/security.py
-------------------
Cryptographic utilities for salted password hashing, JWT token generation,
and FastAPI role-based access control (RBAC) dependencies.
"""

import hashlib
import os
import secrets
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from backend.database import get_db
from backend.models import User

# HTTP Bearer authentication scheme
security_bearer = HTTPBearer(auto_error=False)

# In-memory sliding-window rate limiter store: key -> list of epoch timestamps
_RATE_LIMIT_BUCKETS: Dict[str, List[float]] = defaultdict(list)


def check_rate_limit(key: str, max_requests: int = 15, window_seconds: int = 60) -> None:
    """
    Enforces sliding-window rate limiting to protect sensitive endpoints against
    brute-force and automated credential stuffing attacks.
    """
    now = time.time()
    cutoff = now - window_seconds
    bucket = _RATE_LIMIT_BUCKETS[key]
    _RATE_LIMIT_BUCKETS[key] = [ts for ts in bucket if ts > cutoff]
    if len(_RATE_LIMIT_BUCKETS[key]) >= max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests detected. Please wait a moment before trying again."
        )
    _RATE_LIMIT_BUCKETS[key].append(now)


# ----------------- Salted Password Hashing -----------------

def hash_password(password: str) -> str:
    """
    Hashes a plaintext password using PBKDF2-HMAC-SHA256 with 100,000 iterations and a random salt.
    Format stored: salt$hash
    """
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000
    ).hex()
    return f"{salt}${key}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plaintext password against the stored salt$hash representation.
    Uses constant-time comparison to prevent timing attacks.
    """
    try:
        salt, stored_hash = hashed_password.split("$", 1)
        key = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            100_000
        ).hex()
        return secrets.compare_digest(key, stored_hash)
    except Exception:
        return False


# ----------------- JWT Token Management -----------------

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Encodes claims into a signed JSON Web Token (JWT).
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodes and validates a JWT token. Returns payload or None if invalid or expired.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


# ----------------- FastAPI Auth & RBAC Dependencies -----------------

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency that enforces authentication. Resolves user from Bearer token.
    Raises 401 if credentials are missing, invalid, or expired.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token claims.")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account no longer exists.")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been deactivated.")

    return user


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency that ensures the authenticated user holds an Administrator role.
    Raises 403 Forbidden if user is standard.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges are required to perform this action."
        )
    return current_user
