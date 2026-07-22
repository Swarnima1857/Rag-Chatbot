from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, session, chat
from services.embedding_service import load_company_documents

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
# load company documents automatically when server start
@app.on_event("startup")
async def startup_event():
    print("\n[STARTUP] Loading company documents...")
    total = load_company_documents("company_docs")
    print(f"[STARTUP] {total} chunks ready!")

# connect Auth router 
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(session.router, prefix="/sessions", tags=["Sessions"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])


# Home route
@app.get("/")
def home():
    return {"message": "RAG Chatbot Backend Running!"}