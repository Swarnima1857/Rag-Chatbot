from pydantic import BaseModel

# Upload response ke liye
class UploadResponseSchema(BaseModel):
    message: str
    chunks_created: int

# Chat question ke liye
class ChatRequestSchema(BaseModel):
    session_id: str
    question: str

# Chat response ke liye
class ChatResponseSchema(BaseModel):
    answer: str