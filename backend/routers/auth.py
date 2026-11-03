"""
backend/routers/auth.py
-----------------------
Authentication router: Request Access, Login, Profile, and Account Activation.
"""

from datetime import datetime
import secrets
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, AccessRequest
from backend.schemas import (
    UserLogin,
    TokenResponse,
    UserOut,
    AccessRequestCreate,
    AccessRequestOut,
    AccountActivate,
    SocialLoginRequest
)
from backend.security import (
    verify_password,
    hash_password,
    create_access_token,
    get_current_user,
    check_rate_limit
)
from backend.services.email_service import EmailNotificationService

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/request-access", response_model=AccessRequestOut, status_code=status.HTTP_201_CREATED)
def submit_access_request(
    req_in: AccessRequestCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Public endpoint: Prospective users submit a request for platform access.
    Saved with PENDING status for administrator review.
    Dispatches real-time email notification to anaspatel3130@gmail.com.
    """
    client_ip = request.client.host if request.client else "local"
    check_rate_limit(f"req_access:{client_ip}", max_requests=25, window_seconds=60)
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == req_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An authorized account with this email already exists. Please log in."
        )

    # Check for existing pending request
    existing_req = db.query(AccessRequest).filter(
        AccessRequest.email == req_in.email,
        AccessRequest.status == "PENDING"
    ).first()
    if existing_req:
        return existing_req

    new_req = AccessRequest(
        name=req_in.name,
        email=req_in.email,
        department=req_in.department,
        reason=req_in.reason,
        status="PENDING",
        created_at=datetime.utcnow()
    )
    db.add(new_req)
    db.commit()
    db.refresh(new_req)

    # Dispatch email notification to platform administrator (anaspatel3130@gmail.com)
    req_dict = {
        "id": new_req.id,
        "name": new_req.name,
        "email": new_req.email,
        "department": new_req.department,
        "reason": new_req.reason,
        "created_at": new_req.created_at,
    }
    background_tasks.add_task(EmailNotificationService.send_access_request_alert, req_dict)

    return new_req


@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, request: Request, db: Session = Depends(get_db)):
    """
    Authenticates registered users or administrators.
    Returns signed Bearer JWT token and role metadata.
    """
    client_ip = request.client.host if request.client else "local"
    check_rate_limit(f"login:{client_ip}", max_requests=30, window_seconds=60)
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact your administrator."
        )

    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "full_name": user.full_name,
        "email": user.email,
    }


@router.post("/direct-owner-access", response_model=TokenResponse)
def direct_owner_access(db: Session = Depends(get_db)):
    """
    Direct Owner Access endpoint for Anas S Patel (anaspatel3130@gmail.com).
    Grants instant Master Administrator access without requiring manual password entry.
    """
    owner_email = "anaspatel3130@gmail.com"
    owner = db.query(User).filter(User.email == owner_email).first()
    if not owner:
        owner = User(
            email=owner_email,
            full_name="Anas S Patel (Owner)",
            hashed_password=hash_password("PatelSpark2026!"),
            role="admin",
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.add(owner)
        db.commit()
        db.refresh(owner)
    else:
        if owner.role != "admin" or not owner.is_active:
            owner.role = "admin"
            owner.is_active = True
            db.commit()

    token = create_access_token({"sub": str(owner.id), "email": owner.email, "role": owner.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": owner.role,
        "full_name": owner.full_name,
        "email": owner.email,
    }


@router.post("/social-login", response_model=TokenResponse)
def social_login(payload: SocialLoginRequest, db: Session = Depends(get_db)):
    """
    Seamless 1-Click Social Sign-In (Google, GitHub, Facebook, Guest, or Owner).
    Issues an authenticated session and valid JWT token without requiring approval tokens.
    """
    provider = (payload.provider or "guest").lower().strip()

    # If owner provider or anas's email
    if provider == "owner" or (payload.email and payload.email.lower().strip() == "anaspatel3130@gmail.com"):
        return direct_owner_access(db)

    # Determine user identity based on provider
    if provider == "google":
        email = payload.email or "google.user@patelspark.io"
        full_name = payload.name or "Google User"
    elif provider == "github":
        email = payload.email or "github.user@patelspark.io"
        full_name = payload.name or "GitHub User"
    elif provider == "facebook":
        email = payload.email or "facebook.user@patelspark.io"
        full_name = payload.name or "Facebook User"
    else:
        # Instant Guest / Direct Access
        email = payload.email or f"guest_{secrets.token_hex(4)}@patelspark.io"
        full_name = payload.name or "Guest Analyst"

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            full_name=full_name,
            hashed_password=hash_password(secrets.token_urlsafe(16)),
            role="user",
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "full_name": user.full_name,
        "email": user.email,
    }


@router.get("/me", response_model=UserOut)
def get_authenticated_profile(current_user: User = Depends(get_current_user)):
    """
    Returns the currently authenticated user's profile.
    """
    return current_user


@router.post("/activate")
def activate_account(payload: AccountActivate, db: Session = Depends(get_db)):
    """
    Activates an approved user account via invite token and sets their initial password.
    """
    req = db.query(AccessRequest).filter(
        AccessRequest.invite_token == payload.invite_token,
        AccessRequest.status == "APPROVED"
    ).first()

    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid, expired, or already used invitation token."
        )

    # Check if user already exists
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        user = User(
            email=req.email,
            full_name=payload.full_name or req.name,
            hashed_password=hash_password(payload.password),
            role="user",
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.add(user)
    else:
        user.hashed_password = hash_password(payload.password)
        user.is_active = True

    # Invalidate token
    req.invite_token = None
    db.commit()

    return {"message": "Account successfully activated! You can now log in with your credentials."}
