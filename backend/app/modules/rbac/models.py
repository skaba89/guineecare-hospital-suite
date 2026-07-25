from app.core.datetime import utcnow
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint

from app.db.base import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    code = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    code = Column(String(150), unique=True, index=True, nullable=False)
    name = Column(String(150), nullable=False)
    module = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role_code", "permission_code", name="uq_role_permission"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    role_code = Column(String(100), ForeignKey('roles.code'), nullable=False, index=True)
    permission_code = Column(String(150), ForeignKey('permissions.code'), nullable=False, index=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
