from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from routers.session import get_current_user
from services.embedding_service import (search_company_docs)
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
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ===== HELPER: Generate answer using Ollama (Local, Free) =====
def generate_with_ollama(prompt: str) -> str:
    """
    Sends prompt to local Ollama server (llama3.2 model)
    Runs completely offline — no API key needed
    """
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": "llama3.2",
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()["response"]


# ===== HELPER: Generate answer using OpenAI (Cloud, Paid) =====
def generate_with_gemini(prompt: str) -> str:
    """
    Sends prompt to OpenAI API (gpt-3.5-turbo model)
    Requires OPENAI_API_KEY in .env file
    """
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=400,
            detail="OpenAI API key not configured! Add OPENAI_API_KEY in .env file"
        )

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful company assistant. Answer questions based only on provided company documents."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3
        }
    )
    return response.json()["choices"][0]["message"]["content"]

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
    # Step 5 — Select Moddel and generate Answer (TOGGLE!)
    print(f"\n[MODEL SELECTED]: {request.model}")

    if request.model == "openai":
        answer = generate_with_openai(prompt)
        model_used = "openai/gpt-3.5-turbo"
    else:
        # Default — Ollama use karo
        answer = generate_with_ollama(prompt)
        model_used = "ollama/llama3.2"

    print(f"[ANSWER GENERATED] by {model_used}")

    # Step 4 — MongoDB, Save in mongodb
    chats_collection.insert_one({
        "session_id": request.session_id,
        "user_id": current_user,
        "question": request.question,
        "answer": answer,
        "model_used": model_used,
        "sources": [c["source"] for c in chunks_with_scores],
        "scores": [round(c["score"], 4) for c in chunks_with_scores],
        "created_at": datetime.utcnow()
    })

    return {"answer": answer,
        "sources": [c["source"] for c in chunks_with_scores],
        "model_used": model_used
        }


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