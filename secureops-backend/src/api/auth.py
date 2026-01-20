from datetime import datetime, timedelta, timezone
from uuid import uuid4
import secrets
import hashlib

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.db.session import get_db
from src.db.models import User, RefreshToken
from src.api import schemas
from src.core.security import verify_password, get_password_hash, create_access_token
from src.api.deps import get_current_user

router = APIRouter()

# --- Helpers ---

def create_refresh_token(db: Session, user_id: str, family_id: str = None) -> str:
    """Issue a new rotating refresh token."""
    token_str = secrets.token_urlsafe(64) # Cryptographically secure random string
    
    token_hash = hashlib.sha256(token_str.encode()).hexdigest()
    
    # Use timezone-aware UTC
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    if not family_id:
        family_id = uuid4()
        
    db_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        family_id=family_id,
        expires_at=expires_at,
        created_at=datetime.now(timezone.utc)
    )
    db.add(db_token)
    db.commit()
    
    return token_str

# --- Routes ---

@router.post("/signup", response_model=schemas.UserOut)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Create a new user."""
    # Check existing
    stmt = select(User).where(User.email == user.email)
    existing = db.execute(stmt).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create
    hashed_pwd = get_password_hash(user.password)
    new_user = User(
        email=user.email,
        password_hash=hashed_pwd,
        role=user.role,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=schemas.Token)
def login(response: Response, form_data: schemas.UserLogin, db: Session = Depends(get_db)):
    """Login and set HTTP-only refresh cookie."""
    # 1. Authenticate
    stmt = select(User).where(User.email == form_data.email)
    user = db.execute(stmt).scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    if not user.is_active:
         raise HTTPException(status_code=403, detail="Account inactive")

    # 2. Issue Refresh Token (Cookie)
    raw_refresh = create_refresh_token(db, user.id)
    
    response.set_cookie(
        key="refresh_token",
        value=raw_refresh,
        httponly=True,
        secure=False, # Set to True in HTTPS/Production
        samesite="lax", # Strict causing issues in some dev envs, lax is okay for now
        max_age=7 * 24 * 60 * 60 # 7 days
    )
    
    # 3. Issue Access Token (Response)
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/refresh", response_model=schemas.Token)
def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    """Rotate refresh token and issue new access token."""
    
    # 1. Get Cookie
    refresh_cookie = request.cookies.get("refresh_token")
    if not refresh_cookie:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    
    # 2. Validate
    token_hash = hashlib.sha256(refresh_cookie.encode()).hexdigest()
    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    db_token = db.execute(stmt).scalar_one_or_none()
    
    # Reuse Detection / Theft
    if not db_token:
        # If valid format but not in DB (or already rotated), could be attack.
        # Ideally we find the family and revoke all? Hard without look up.
        raise HTTPException(status_code=401, detail="Invalid refresh token")
        
    if db_token.revoked:
        # Reuse attempted! Security Alert!
        # Revoke entire family
        db.query(RefreshToken).filter(RefreshToken.family_id == db_token.family_id).update({"revoked": True})
        db.commit()
        raise HTTPException(status_code=401, detail="Token reuse detected. Session terminated.")
        
    if db_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token expired")

    # 3. Rotate (Revoke Old, Create New)
    # Mark user active
    user = db.query(User).filter(User.id == db_token.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Revoke old
    db_token.revoked = True
    db_token.last_used_at = datetime.now(timezone.utc)
    
    # Create new (Same family)
    new_refresh_raw = create_refresh_token(db, user.id, family_id=db_token.family_id)
    
    # Set Cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_raw,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 60 * 60
    )
    
    # Issue Access Token
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    """Revoke refresh token."""
    refresh_cookie = request.cookies.get("refresh_token")
    if refresh_cookie:
        token_hash = hashlib.sha256(refresh_cookie.encode()).hexdigest()
        db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).update({"revoked": True})
        db.commit()
    
    response.delete_cookie("refresh_token")
    return {"message": "Logged out"}

@router.get("/me", response_model=schemas.UserOut)
def me(user: User = Depends(get_current_user)):
    """Get current user context."""
    return user
