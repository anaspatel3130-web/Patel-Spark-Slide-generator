"""
backend/routers/admin.py
------------------------
Administrator management router: Review pending access requests, approve/reject candidates,
and manage authorized user accounts.
"""

from datetime import datetime
import secrets
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from backend.config import CUSTOM_TEMPLATE_PATH
from backend.database import get_db
from backend.models import User, AccessRequest
from backend.schemas import AccessRequestOut, AccessRequestAction, UserOut
from backend.security import get_current_admin

router = APIRouter(prefix="/api/admin", tags=["Administrator Operations"])


@router.get("/requests", response_model=List[AccessRequestOut])
def list_access_requests(
    status_filter: str = "ALL",
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Returns access requests submitted by prospective users.
    Filtered by status ('PENDING', 'APPROVED', 'REJECTED', or 'ALL').
    """
    query = db.query(AccessRequest).order_by(AccessRequest.created_at.desc())
    if status_filter != "ALL":
        query = query.filter(AccessRequest.status == status_filter.upper())
    return query.all()


@router.post("/requests/{request_id}/action", response_model=AccessRequestOut)
def review_access_request(
    request_id: int,
    action_in: AccessRequestAction,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Approve or Reject a pending access request.
    If APPROVED: Generates a secure invite activation token.
    """
    req = db.query(AccessRequest).filter(AccessRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.")

    action = action_in.action.upper()
    status_value = "APPROVED" if action == "APPROVE" else "REJECTED"
    req.status = status_value
    req.reviewed_at = datetime.utcnow()

    if status_value == "APPROVED":
        req.invite_token = secrets.token_urlsafe(32)
    else:
        req.invite_token = None

    db.commit()
    db.refresh(req)
    return req


@router.get("/users", response_model=List[UserOut])
def list_authorized_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Returns all registered platform users.
    """
    return db.query(User).order_by(User.created_at.desc()).all()


@router.post("/users/{user_id}/toggle-status", response_model=UserOut)
def toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Activates or revokes user access. Administrators cannot deactivate themselves.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot deactivate their own account."
        )

    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    return user


@router.get("/template/status")
def get_template_status(admin: User = Depends(get_current_admin)):
    """
    Checks if a custom authorized PowerPoint template is currently installed.
    """
    has_custom = CUSTOM_TEMPLATE_PATH.exists()
    return {
        "has_custom_template": has_custom,
        "template_name": CUSTOM_TEMPLATE_PATH.name if has_custom else "Neutral Executive Theme (Default)",
        "file_size": CUSTOM_TEMPLATE_PATH.stat().st_size if has_custom else None
    }


@router.post("/template")
async def upload_corporate_template(
    file: UploadFile = File(...),
    admin: User = Depends(get_current_admin)
):
    """
    Allows an administrator to upload an authorized corporate PowerPoint template (.pptx).
    """
    ext = Path(file.filename).suffix.lower()
    if ext != ".pptx":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Corporate template must be a valid .pptx PowerPoint file."
        )

    content = await file.read()
    with open(CUSTOM_TEMPLATE_PATH, "wb") as f:
        f.write(content)

    return {
        "message": "Corporate PowerPoint template successfully uploaded and activated.",
        "filename": file.filename,
        "size_bytes": len(content)
    }


@router.delete("/template")
def remove_corporate_template(admin: User = Depends(get_current_admin)):
    """
    Removes custom corporate template and reverts to the default neutral executive design.
    """
    if CUSTOM_TEMPLATE_PATH.exists():
        CUSTOM_TEMPLATE_PATH.unlink()
    return {"message": "Custom template removed. System restored to default neutral executive design."}

