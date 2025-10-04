"""
Authentication and security utilities
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.models import User, UserSession
import secrets
import logging

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Security scheme
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate user with username and password"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = verify_token(token)
        if payload is None:
            raise credentials_exception
        
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    return user


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Return the authenticated user if a valid bearer token is supplied."""

    authorization: str | None = request.headers.get("Authorization")
    if not authorization:
        return None

    scheme, token = get_authorization_scheme_param(authorization)
    if not token or scheme.lower() != "bearer":
        return None

    payload = verify_token(token)
    if not payload or payload.get("type") != "access":
        return None

    username: str | None = payload.get("sub")
    if not username:
        return None

    return db.query(User).filter(User.username == username).first()

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Get current admin user"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

def create_user_session(db: Session, user: Optional[User], ip_address: str = None, user_agent: str = None) -> UserSession:
    """Create a new user session"""
    session_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=30)  # 30 day session
    
    session = UserSession(
        user_id=user.id if user else None,
        session_token=session_token,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=expires_at
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return session

def get_user_from_session(db: Session, session_token: str) -> Optional[User]:
    """Get user from session token"""
    session = db.query(UserSession).filter(
        UserSession.session_token == session_token,
        UserSession.is_active == True,
        UserSession.expires_at > datetime.utcnow()
    ).first()
    
    if not session or not session.user_id:
        return None
    
    return db.query(User).filter(User.id == session.user_id).first()

def log_user_activity(db: Session, user: Optional[User], activity_type: str, details: dict = None):
    """Log user activity for analytics"""
    try:
        from app.core.models import SystemLog
        
        log_entry = SystemLog(
            level="info",
            component="user_activity",
            message=f"User activity: {activity_type}",
            user_id=user.id if user else None,
            extra_data=details or {}
        )
        
        db.add(log_entry)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to log user activity: {e}")

def require_auth(allow_anonymous: bool = False):
    """Decorator to require authentication (optional anonymous)"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would be implemented as a dependency in FastAPI
            pass
        return wrapper
    return decorator
