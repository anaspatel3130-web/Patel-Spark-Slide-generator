"""
backend/models.py
-----------------
SQLAlchemy ORM models representing Users, Access Requests, and Presentation Generation History.
"""

from datetime import datetime
import uuid
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="user", nullable=False)  # 'admin' or 'user'
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    presentations = relationship("PresentationRecord", back_populates="user", cascade="all, delete-orphan")


class AccessRequest(Base):
    __tablename__ = "access_requests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), index=True, nullable=False)
    department = Column(String(255), nullable=True)
    reason = Column(Text, nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)  # 'PENDING', 'APPROVED', 'REJECTED'
    invite_token = Column(String(100), unique=True, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PresentationRecord(Base):
    __tablename__ = "presentation_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_filename = Column(String(255), nullable=False)
    presentation_title = Column(String(255), nullable=False)
    slide_count = Column(Integer, nullable=False)
    pptx_filename = Column(String(255), nullable=False)
    insights_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="presentations")
