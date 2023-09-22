from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.openapi.models import OAuthFlowPassword
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import Session, sessionmaker
from pydantic import BaseModel
import pyotp  # For OTP generation
import re  # For email and password validation
import logging  # For logging
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

# Create a FastAPI instance
app = FastAPI()

# Database Configuration
DATABASE_URL = "mysql://your_db_user:your_db_password@localhost/your_db_name"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Database Models
class User(BaseModel):
    id: int
    full_name: str
    email: str
    password: str
    otp_secret: str
    status: str

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models for request input validation
class UserCreateRequest(BaseModel):
    full_name: str
    email: str
    password: str

class UserLoginRequest(BaseModel):
    email: str
    password: str

class UserVerifyOTPRequest(BaseModel):
    otp_code: str

# Password hashing and verification
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Generate an OTP secret
def generate_otp_secret():
    return pyotp.random_base32()

# Create a new user with OTP secret and pending status
def create_user(db: Session, user_create_request: UserCreateRequest):
    hashed_password = pwd_context.hash(user_create_request.password)
    otp_secret = generate_otp_secret()
    new_user = User(
        full_name=user_create_request.full_name,
        email=user_create_request.email,
        password=hashed_password,
        otp_secret=otp_secret,
        status="pending",
    )
    db.add(new_user)
    db.commit()
    return new_user

# Email validation regex
EMAIL_REGEX = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')

# Password validation regex (at least 8 characters, at least one uppercase letter, one lowercase letter, and one digit)
PASSWORD_REGEX = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$')

# Initialize logger
logging.basicConfig(filename='app.log', level=logging.INFO)

# JWT Configuration
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Create access token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Verify OTP code
def verify_otp(otp_code: str, user: User):
    totp = pyotp.TOTP(user.otp_secret)
    return totp.verify(otp_code)

# API Endpoint to Register a New User
@app.post("/register", response_model=User)
def register(
    user_create_request: UserCreateRequest,
    db: Session = Depends(get_db)
):
    # Validate email and password format
    if not EMAIL_REGEX.match(user_create_request.email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    if not PASSWORD_REGEX.match(user_create_request.password):
        raise HTTPException(status_code=400, detail="Weak password. Ensure it meets complexity requirements.")

    # Create a new user
    new_user = create_user(db, user_create_request)

    # Generate an OTP URI (useful for generating QR code)
    otp_uri = pyotp.totp.TOTP(new_user.otp_secret).provisioning_uri(new_user.email, issuer_name='YourApp')

    # Send the OTP URI to the user (e.g., via email)
    send_otp_setup_instructions(new_user.email, otp_uri)  # Implement OTP setup instructions sending

    return new_user

# API Endpoint to Log In
@app.post("/login", response_model=User)
def login(
    user_login_request: UserLoginRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter_by(email=user_login_request.email).first()

    if not user or not pwd_context.verify(user_login_request.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if user.status != "active":
        raise HTTPException(status_code=401, detail="User not active")

    # Create an access token
    access_token = create_access_token({"sub": user.email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}

# API Endpoint to Verify OTP
@app.post("/verify-otp", response_model=User)
def verify_otp(
    user_verify_otp_request: UserVerifyOTPRequest,
    current_user_email: str = Depends(get_jwt_identity),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter_by(email=current_user_email).first()

    if not user or user.status != 'pending':
        raise HTTPException(status_code=401, detail="Invalid user or user status")

    if verify_otp(user_verify_otp_request.otp_code, user):
        user.status = 'active'
        db.commit()
        return user
    else:
        raise HTTPException(status_code=401, detail="Invalid OTP code")

if __name__ == '__main__':
    app.run(debug=True)
