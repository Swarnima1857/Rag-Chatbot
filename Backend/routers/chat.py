from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from routers.session import get_current_user
from services.embedding_service import process_pdf, get_vectorstore
from schemas.chat_schema import ChatRequestSchema
from database.db import chats_collection, sessions_collection
from langchain_ollama import ChatOllama
from langchain.chains import RetrievalQA
from bson import ObjectId
from datetime import datetime
import os
import shutil

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ===== PDF UPLOAD ROUTE =====
@router.post("/upload/{session_id}")
def upload_pdf(
    session_id: str,
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user)
):
    # Check which user's session is this
    session = sessions_collection.find_one({
        "_id": ObjectId(session_id),
        "user_id": current_user
    })
    if not session:
        raise HTTPException(status_code=404, detail="Session not found!")

    # save pdf in disk
    file_path = os.path.join(UPLOAD_DIR, f"{session_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # process pdf — make chunks and save in Chromadb
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
    # Check which user's session is this
    session = sessions_collection.find_one({
        "_id": ObjectId(request.session_id),
        "user_id": current_user
    })
    if not session:
        raise HTTPException(status_code=404, detail="Session not found!")

    # Vectorstore (retrive saved dat from Chromadb)
    vectorstore = get_vectorstore(request.session_id)

    # setup Ollama LLM
    llm = ChatOllama(model="llama3.2")

    # make RAG chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vectorstore.as_retriever()
    )

    # answer of a question
    result = qa_chain.invoke(request.question)
    answer = result["result"]

    # Save Chat History in Mongodb
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