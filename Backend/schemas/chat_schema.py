from typing import Optional
from pydantic import BaseModel


# For Chat Question
class ChatRequestSchema(BaseModel):
    session_id: str
    question: str
    model: Optional[str] = "ollama"  # "ollama" or "openai" — default ollama

# For Chat Response
class ChatResponseSchema(BaseModel):
    answer: str
    sources: list = []
    model_used: str = ""
