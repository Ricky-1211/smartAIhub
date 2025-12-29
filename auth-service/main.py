"""
Authentication & Authorization Service
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared.config import (
    JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_REFRESH_TOKEN_EXPIRE_DAYS, POSTGRES_HOST, POSTGRES_PORT,
    POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, ALLOWED_ORIGINS
)
from shared.utils import create_response, validate_email, log_error
import enum

app = FastAPI(title="Auth Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
    SERVICE = "service"


# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), default=UserRole.USER)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Pydantic Models
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: Optional[str]
    role: str
    is_active: bool
    
    class Config:
        from_attributes = True  # Pydantic v2
        from_orm = True  # Pydantic v1 compatibility


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Password utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password using bcrypt directly"""
    try:
        # Convert to bytes
        plain_bytes = plain_password.encode('utf-8')
        if len(plain_bytes) > 72:
            plain_bytes = plain_bytes[:72]
        
        hashed_bytes = hashed_password.encode('utf-8')
        
        # Use bcrypt directly
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except Exception:
        # Fallback to passlib if bcrypt fails
        return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password with bcrypt, ensuring it's within 72-byte limit"""
    # Ensure password is a string
    if not isinstance(password, str):
        password = str(password)
    
    # Convert to bytes for bcrypt
    password_bytes = password.encode('utf-8')
    
    # Bcrypt has a strict 72-byte limit - truncate if necessary
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    # Use bcrypt directly to avoid passlib issues
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Return as string (bcrypt returns bytes)
    return hashed.decode('utf-8')


# JWT utilities
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return TokenData(
            user_id=payload.get("sub"),
            email=payload.get("email"),
            role=payload.get("role")
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


# Authentication dependency
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    token_data = decode_token(token)
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    return current_user


# Routes
@app.get("/health")
async def health_check():
    return create_response(True, "Auth service is healthy")


@app.post("/register", response_model=dict)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """User registration"""
    try:
        # Check if user exists
        if db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        if db.query(User).filter(User.username == user_data.username).first():
            raise HTTPException(
                status_code=400,
                detail="Username already taken"
            )
        
        # Create user
        import uuid
        # Ensure password is a string and validate length
        password = str(user_data.password) if user_data.password else ""
        if not password:
            raise HTTPException(
                status_code=400,
                detail="Password is required"
            )
        
        # Hash password (function handles 72-byte limit internally)
        hashed = get_password_hash(password)
        
        user = User(
            id=str(uuid.uuid4()),
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed,
            full_name=user_data.full_name,
            role=UserRole.USER
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Handle Pydantic v1 and v2 compatibility
        try:
            # Try Pydantic v2 method first
            user_response = UserResponse.model_validate(user)
            user_dict = user_response.model_dump()
        except AttributeError:
            # Fallback to Pydantic v1
            try:
                user_response = UserResponse.from_orm(user)
                user_dict = user_response.dict()
            except AttributeError:
                # Manual conversion if both fail
                user_dict = {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name,
                    "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
                    "is_active": user.is_active
                }
        
        return create_response(
            True,
            "User registered successfully",
            user_dict
        )
    except HTTPException:
        raise
    except Exception as e:
        log_error("auth-service", e, {"endpoint": "/register", "email": user_data.email})
        raise HTTPException(
            status_code=500,
            detail=f"Registration failed: {str(e)}"
        )


@app.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """User login"""
    user = db.query(User).filter(
        (User.username == form_data.username) | (User.email == form_data.username)
    ).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email, "role": user.role.value}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.id, "email": user.email, "role": user.role.value}
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )


@app.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Refresh access token"""
    token_data = decode_token(refresh_token)
    if token_data.user_id is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email, "role": user.role.value}
    )
    new_refresh_token = create_refresh_token(
        data={"sub": user.id, "email": user.email, "role": user.role.value}
    )
    
    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token
    )


@app.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    try:
        # Try Pydantic v2 method first
        try:
            user_response = UserResponse.model_validate(current_user)
            user_dict = user_response.model_dump()
        except AttributeError:
            # Fallback to Pydantic v1
            try:
                user_response = UserResponse.from_orm(current_user)
                user_dict = user_response.dict()
            except AttributeError:
                # Manual conversion if both fail
                user_dict = {
                    "id": current_user.id,
                    "email": current_user.email,
                    "username": current_user.username,
                    "full_name": current_user.full_name,
                    "role": current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role),
                    "is_active": current_user.is_active
                }
        
        return create_response(True, "User information retrieved", user_dict)
    except Exception as e:
        log_error("auth-service", e, {"endpoint": "/me"})
        raise HTTPException(status_code=500, detail="Failed to get user information")


@app.get("/verify")
async def verify_token(token: str = Depends(oauth2_scheme)):
    """Verify JWT token"""
    token_data = decode_token(token)
    return create_response(True, "Token is valid", token_data.dict())


# Initialize database
@app.on_event("startup")
async def startup():
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database connection successful")
    except Exception as e:
        print(f"⚠️  Database connection failed: {e}")
        print("⚠️  Please ensure PostgreSQL is running on localhost:5432")
        print("⚠️  Start PostgreSQL with: docker run -d --name postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:15-alpine")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

