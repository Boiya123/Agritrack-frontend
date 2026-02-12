# Click dropdown on line 2 for briefing about the file
"""
Responsibility: Handles who the user is and what they are allowed to do. Nothing else.

What goes here:

- User registration

- User login

- Token generation and refresh

- Role validation endpoints

- Password reset and change

- Logout and token invalidation

What must NOT go here:

- Farm logic

- Batch creation

- Product creation

- Any traceability data

"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt

from app.core.security import hash_password, verify_password, create_access_token
from app.core.config import settings
from app.database.session import get_db
from app.models.user_model import User, UserRole
from app.schemas.user_schema import UserRegister, UserLogin


router = APIRouter(prefix="/auth", tags=["authentication"])

# Store for token blacklist (in production, use Redis)
token_blacklist = set()


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    Extracts token from Authorization: Bearer <token> header.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = parts[1]

    if token in token_blacklist:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been invalidated"
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    User registration endpoint.
    Creates a new user with provided credentials and role.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    hashed_pwd = hash_password(user_data.password)
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=hashed_pwd,
        role=UserRole[user_data.role]
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "id": new_user.id,
        "email": new_user.email,
        "name": new_user.name,
        "role": new_user.role.value
    }


@router.post("/login")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    User login endpoint.
    Validates credentials and returns an access token.
    """
    # Find user by email
    user = db.query(User).filter(User.email == user_data.email).first()

    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Generate access token
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value},
        settings=settings
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "role": user.role.value
    }


@router.post("/refresh")
async def refresh_token(current_user: User = Depends(get_current_user)):
    """
    Token refresh endpoint.
    Generates a new access token for an authenticated user.
    """
    access_token = create_access_token(
        data={"sub": str(current_user.id), "role": current_user.role.value},
        settings=settings
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/validate-role/{required_role}")
async def validate_role(required_role: str, current_user: User = Depends(get_current_user)):
    """
    Role validation endpoint.
    Checks if the current user has the required role.
    """
    if current_user.role.value != required_role.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User role '{current_user.role.value}' does not match required role '{required_role.lower()}'"
        )

    return {
        "user_id": current_user.id,
        "role": current_user.role.value,
        "is_authorized": True
    }


@router.post("/password-reset")
def password_reset(email: str, db: Session = Depends(get_db)):
    """
    Password reset endpoint.
    In production, this should send a reset link via email.
    """
    user = db.query(User).filter(User.email == email).first()

    if not user:
        # Don't reveal if email exists for security
        return {"message": "If email exists, a reset link will be sent"}

    # In production, generate a secure reset token and send via email
    # For now, we'll return a placeholder message
    return {"message": "Password reset link sent to email"}


@router.put("/password-change")
async def password_change(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Password change endpoint.
    Allows authenticated users to change their password.
    """
    # Verify old password
    if not verify_password(old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Old password is incorrect"
        )

    # Update password
    current_user.hashed_password = hash_password(new_password)
    current_user.updated_at = datetime.utcnow()

    db.add(current_user)
    db.commit()

    return {"message": "Password changed successfully"}


@router.post("/logout")
async def logout(
    authorization: Optional[str] = Header(None),
    current_user: User = Depends(get_current_user)
):
    """
    Logout endpoint.
    Invalidates the user's token by adding it to a blacklist.
    """
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
            token_blacklist.add(token)

    return {
        "message": "Successfully logged out",
        "user_id": current_user.id
    }


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information endpoint.
    Returns details about the authenticated user.
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role.value,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at
    }
