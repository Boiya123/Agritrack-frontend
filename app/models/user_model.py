from sqlalchemy import Column, Integer, String, Enum
from app.database.base import Base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import DateTime, func
import uuid
import enum

# Defines user roles
class UserRole(enum.Enum):
    FARMER = "farmer"
    REGULATOR = "regulator"
    SUPPLIER = "supplier"
    ADMIN = "admin"

# User model for ORM
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Representation method for debugging
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"