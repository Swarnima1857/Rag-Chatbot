from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from routers.session import get_current_user
from services.embedding_service import ( search_similar_chunks, search_company_docs)
from schemas.chat_schema import ChatRequestSchema
from database.db import chats_collection, sessions_collection
from bson import ObjectId
from datetime import datetime
import requests
import os
import shutil
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

router = APIRouter()
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")


# CHAT ROUTE - ASK QUESTION - from Company Docs
@router.post("/ask")
def ask_question(
    request: ChatRequestSchema,
    current_user: str = Depends(get_current_user)
):
    # Check, which users session is this ?
    session = sessions_collection.find_one({
        "_id": ObjectId(request.session_id),
        "user_id": current_user
    })
    if not session:
        raise HTTPException(
            status_code=404, 
            detail="Session not found!"
            )

        # find relevant chunks from Company docs
    chunks_with_scores = search_company_docs(request.question)

    if not chunks_with_scores:
        return {
            "answer": "Sorry, I couldn't find relevant information in our company documents.",
            "sources": []
        }  

     # make Context — show source too
    context_parts = []
    for chunk in chunks_with_scores:
        context_parts.append(
            f"[Source: {chunk['source']}]\n{chunk['text']}"
        )

    # Step 2 — Chunks ko context mein jodo
    context = "\n\n".join(context_parts)

    # Step 3 —  send promt to ollama
    prompt = f"""You are a helpful company assistant.
Answer the question based ONLY on the provided company documents.If the answer is not in the documents, say "I don't have information about this
    
Company Documents Context:
{context}

Question: {request.question}

Answer:"""
    # get response from Ollama
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": "llama3.2",
            "prompt": prompt,
            "stream": False
        }
    )
    answer = response.json()["response"]

    # Step 4 — MongoDB, Save in mongodb
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
            "sources": chat.get("sources", []),
            "created_at": str(chat["created_at"])
        })
    return result