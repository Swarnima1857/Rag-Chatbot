from fastapi import APIRouter, HTTPException
from database.db import users_collection
from schemas.auth_schema import SignupSchema, LoginSchema, TokenSchema
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta

# ===== CONFIGURATION =====
SECRET_KEY = "Sw@rnima#RAG$2024!SecureKey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# ===== SETUP =====
router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ===== HELPER FUNCTIONS =====

# Password hash karna
def hash_password(password: str):
    return pwd_context.hash(password)

# Password verify karna
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

# Token banana
def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ===== ROUTES =====

# Signup API
@router.post("/signup")
def signup(user: SignupSchema):
    # Email already registered hai?
    existing_user = users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered!")

    # Password hash karo
    hashed_pw = hash_password(user.password)

    # Database mein save karo
    new_user = {
        "username": user.username,
        "email": user.email,
        "password": hashed_pw,
        "created_at": datetime.utcnow()
    }
    users_collection.insert_one(new_user)
    return {"message": "Signup successful!"}


# Login API
@router.post("/login", response_model=TokenSchema)
def login(user: LoginSchema):
    # Database mein user dhundo
    db_user = users_collection.find_one({"email": user.email})
    if not db_user:
        raise HTTPException(status_code=400, detail="Email not found!")

    # Password check karo
    if not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=400, detail="Wrong password!")

    # Token banao aur bhejo
    token = create_token({"sub": str(db_user["_id"]), "email": db_user["email"]})
    return {"access_token": token, "token_type": "bearer"}