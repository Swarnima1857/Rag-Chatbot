from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from routers.session import get_current_user
from services.embedding_service import process_pdf, search_similar_chunks
from schemas.chat_schema import ChatRequestSchema
from database.db import chats_collection, sessions_collection
from bson import ObjectId
from datetime import datetime
import requests
import os
import shutil

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

OLLAMA_URL = "http://localhost:11434"


# ===== PDF UPLOAD ROUTE =====
@router.post("/upload/{session_id}")
def upload_pdf(
    session_id: str,
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user)
):
    # Check karo session is user ka hai
    session = sessions_collection.find_one({
        "_id": ObjectId(session_id),
        "user_id": current_user
    })
    if not session:
        raise HTTPException(status_code=404, detail="Session not found!")

    # PDF ko disk pe save karo
    file_path = os.path.join(UPLOAD_DIR, f"{session_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # PDF process karo — chunks bana ke Qdrant mein save karo
    chunks_count = process_pdf(file_path, session_id)

    return {
        "message": "PDF processed successfully!",
        "chunks_created": chunks_count
    }


# ===== CHAT ROUTE =====
@router.post("/ask")
def ask_question(
    request: ChatRequestSchema,
    current_user: str = Depends(get_current_user)
):
    # Check karo session is user ka hai
    session = sessions_collection.find_one({
        "_id": ObjectId(request.session_id),
        "user_id": current_user
    })
    if not session:
        raise HTTPException(status_code=404, detail="Session not found!")

    # Step 1 — Qdrant se relevant chunks dhundho
    relevant_chunks = search_similar_chunks(request.question, request.session_id)

    # Step 2 — Chunks ko context mein jodo
    context = "\n\n".join(relevant_chunks)

    # Step 3 — Ollama ko prompt bhejo
    prompt = f"""Use the following context to answer the question.
    
Context:
{context}

Question: {request.question}

Answer:"""

    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": "llama3.2",
            "prompt": prompt,
            "stream": False
        }
    )
    answer = response.json()["response"]

    # Step 4 — MongoDB mein save karo
    chats_collection.insert_one({
        "session_id": request.session_id,
        "user_id": current_user,
        "question": request.question,
        "answer": answer,
        "created_at": datetime.utcnow()
    })

    return {"answer": answer}


# ===== CHAT HISTORY ROUTE =====
@router.get("/history/{session_id}")
def get_chat_history(
    session_id: str,
    current_user: str = Depends(get_current_user)
):
    chats = chats_collection.find({
        "session_id": session_id,
        "user_id": current_user
    })
    result = []
    for chat in chats:
        result.append({
            "question": chat["question"],
            "answer": chat["answer"],
            "created_at": str(chat["created_at"])
        })
    return result