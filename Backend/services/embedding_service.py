import requests
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
import pypdf
import uuid

# Qdrant Cloud connection
QDRANT_URL = "https://89d9406d-d4ca-4cc7-91d6-79a3d56079c4.sa-east-1-0.aws.cloud.qdrant.io"  
QDRANT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6ZDhiMjBhYTItN2MxMi00ZDc4LWE0ZjMtODJjZWM0OTNmZDc3In0.m3Fm74FEEvo3VwV2ugFd1t1xYdRpES1_X7tw0fBJRg0" 
OLLAMA_URL = "http://localhost:11434"

# Qdrant client
client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)


# converting text in embeddings by using Ollama
def get_embedding(text: str):
    response = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": "nomic-embed-text", "prompt": text}
    )
    return response.json()["embedding"]


# retrieve text from pdf
def extract_text_from_pdf(pdf_path: str):
    reader = pypdf.PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text


# break text in chunks
def create_chunks(text: str, chunk_size: int = 500, overlap: int = 50):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


# process pdf — make chunks and save in qdrants
def process_pdf(pdf_path: str, session_id: str):
    collection_name = f"session_{session_id}"

    # Step 1 — retrirve text from pdf
    text = extract_text_from_pdf(pdf_path)
    if not text.strip():
        raise ValueError("PDF mein koi text nahi mila!")

    # Step 2 — Make Chunks
    chunks = create_chunks(text)

    # Step 3 — make collection in Qdrant
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=768, distance=Distance.COSINE)
    )

    # Step 4 — Make embeddings of every Chunks and save
    points = []
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={"text": chunk, "chunk_index": i}
            )
        )

    # Step 5 — save in qdrant
    client.upsert(
        collection_name=collection_name,
        points=points
    )

    return len(chunks)


# find relevent chunks for question
def search_similar_chunks(question: str, session_id: str, top_k: int = 3):
    collection_name = f"session_{session_id}"

    # make embeddings of question
    question_embedding = get_embedding(question)

    # search in qdrant
    results = client.search(
        collection_name=collection_name,
        query_vector=question_embedding,
        limit=top_k
    )

    # Return Relevent chunks
    return [result.payload["text"] for result in results]