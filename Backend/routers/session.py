from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from database.db import sessions_collection
from schemas.session_schema import CreateSessionSchema
from jose import jwt, JWTError
from datetime import datetime
from bson import ObjectId

# ===== CONFIGURATION =====
SECRET_KEY = "Sw@rnima#RAG$2024!SecureKey"  # auth.py wali same key
ALGORITHM = "HS256"

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ===== HELPER FUNCTION =====

# Token se current user nikalna
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token!")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token!")


# ===== ROUTES =====

# Naya session banao
@router.post("/create")
def create_session(
    session: CreateSessionSchema,
    current_user: str = Depends(get_current_user)
):
    new_session = {
        "user_id": current_user,
        "title": session.title,
        "created_at": datetime.utcnow()
    }
    result = sessions_collection.insert_one(new_session)
    return {
        "session_id": str(result.inserted_id),
        "title": session.title,
        "created_at": str(new_session["created_at"])
    }


# User ke saare sessions dekho
@router.get("/all")
def get_all_sessions(current_user: str = Depends(get_current_user)):
    sessions = sessions_collection.find({"user_id": current_user})
    result = []
    for session in sessions:
        result.append({
            "session_id": str(session["_id"]),
            "title": session["title"],
            "created_at": str(session["created_at"])
        })
    return result


# Session delete karo
@router.delete("/{session_id}")
def delete_session(
    session_id: str,
    current_user: str = Depends(get_current_user)
):
    session = sessions_collection.find_one({
        "_id": ObjectId(session_id),
        "user_id": current_user
    })
    if not session:
        raise HTTPException(status_code=404, detail="Session not found!")

    sessions_collection.delete_one({"_id": ObjectId(session_id)})
    return {"message": "Session deleted!"}