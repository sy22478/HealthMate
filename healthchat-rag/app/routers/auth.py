from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, Conversation
from app.services.auth import AuthService
from app.config import settings
from pydantic import BaseModel, EmailStr
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.utils.audit_log import log_audit_event

router = APIRouter()
auth_service = AuthService(settings.secret_key)
security = HTTPBearer()

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    age: int
    medical_conditions: str = ""
    medications: str = ""

class UserLogin(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db), request: Request = None):
    encryption_manager = request.app.state.encryption_manager if request else None
    user_email = user.email
    try:
        existing = db.query(User).filter(User.email == user.email).first()
        if existing:
            log_audit_event(user_email, "register_failure", "Email already registered")
            raise HTTPException(status_code=400, detail="Email already registered")
        hashed_password = auth_service.get_password_hash(user.password)
        db_user = User(
            email=user.email,  # store plaintext
            hashed_password=hashed_password,
            full_name=encryption_manager.encrypt(user.full_name) if encryption_manager else user.full_name,
            age=user.age,
            medical_conditions=encryption_manager.encrypt(user.medical_conditions) if encryption_manager else user.medical_conditions,
            medications=encryption_manager.encrypt(user.medications) if encryption_manager else user.medications
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        log_audit_event(user_email, "register_success", "User registered successfully")
        return {"message": "User registered successfully"}
    except Exception as e:
        log_audit_event(user_email, "register_error", str(e))
        raise

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db), request: Request = None):
    encryption_manager = request.app.state.encryption_manager if request else None
    user_email = user.email
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not auth_service.verify_password(user.password, db_user.hashed_password):
        log_audit_event(user_email, "login_failure", "Invalid credentials")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = auth_service.create_access_token({"sub": user.email, "user_id": db_user.id})
    log_audit_event(user_email, "login_success", "User logged in successfully")
    return {"access_token": access_token, "token_type": "bearer"}

# Helper to get user from JWT
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db), request: Request = None):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        # Decrypt sensitive fields
        encryption_manager = request.app.state.encryption_manager if request else None
        if encryption_manager:
            # user.email is plaintext
            user.full_name = encryption_manager.decrypt(user.full_name)
            user.medical_conditions = encryption_manager.decrypt(user.medical_conditions)
            user.medications = encryption_manager.decrypt(user.medications)
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token") 