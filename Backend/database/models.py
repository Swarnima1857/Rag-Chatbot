from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class User(BaseModel):
    username: str
    email: str
    password: str

class Session(BaseModel):
    user_id: str
    title: str
    created_at: datetime = datetime.now()

class ChatMessage(BaseModel):
    session_id: str
    user_id: str
    question: str
    answer: str
    created_at: datetime = datetime.now()