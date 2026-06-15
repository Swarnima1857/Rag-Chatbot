from pydantic import BaseModel

# for amking new session
class CreateSessionSchema(BaseModel):
    title: str = "New Chat"

# for session response
class SessionResponseSchema(BaseModel):
    session_id: str
    title: str
    created_at: str