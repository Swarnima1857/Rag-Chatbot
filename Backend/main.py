from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, session, chat

# make FastAPI 
app = FastAPI(title="RAG Chatbot API")

# setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# connect Auth router 
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(session.router, prefix="/sessions", tags=["Sessions"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])


# Home route
@app.get("/")
def home():
    return {"message": "RAG Chatbot Backend Running!"}