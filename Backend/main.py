from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, session

# FastAPI app banao
app = FastAPI(title="RAG Chatbot API")

# CORS setup karo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth router connect karo
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(session.router, prefix="/sessions", tags=["Sessions"])


# Home route
@app.get("/")
def home():
    return {"message": "RAG Chatbot Backend Running!"}