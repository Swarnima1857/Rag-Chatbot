import requests
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
import pypdf
import uuid

# Qdrant Cloud connection details
QDRANT_URL = "https://89d9406d-d4ca-4cc7-91d6-79a3d56079c4.sa-east-1-0.aws.cloud.qdrant.io"
QDRANT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6Y2ExMGNhNjctZTU0Yi00ZjcyLWFlN2MtNTQzNTc5NzJkOWZlIn0.c3P_inmM4dQwKawLpqV7X004cSEMEfjZdB_zICvVjSs"  # Replace with new API key
OLLAMA_URL = "http://localhost:11434"

# Create Qdrant client — connects to Qdrant Cloud
client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    check_compatibility=False  # Skips version mismatch warning
)


# Convert text to embedding using Ollama API
def get_embedding(text: str):
    response = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": "nomic-embed-text", "prompt": text}
    )
    return response.json()["embedding"]


# Extract all text from PDF file
def extract_text_from_pdf(pdf_path: str):
    reader = pypdf.PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text


# Break large text into smaller chunks with overlap
def create_chunks(text: str, chunk_size: int = 500, overlap: int = 50):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


# Main function — process PDF and save embeddings in Qdrant
def process_pdf(pdf_path: str, session_id: str):
    collection_name = f"session_{session_id}"

    # Step 1 — Extract text from PDF
    text = extract_text_from_pdf(pdf_path)
    if not text.strip():
        raise ValueError("No text found in PDF!")

    # Step 2 — Break text into chunks
    chunks = create_chunks(text)

    # Step 3 — Create a new collection in Qdrant for this session
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=768, distance=Distance.COSINE)
    )

    # Step 4 — Generate embeddings for each chunk and prepare points
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

    # Step 5 — Save all points to Qdrant
    client.upsert(
        collection_name=collection_name,
        points=points
    )

    return len(chunks)


# Search for relevant chunks based on user question
def search_similar_chunks(question: str, session_id: str, top_k: int = 3):
    collection_name = f"session_{session_id}"

    # Convert question to embedding
    question_embedding = get_embedding(question)

    # Search Qdrant for most similar chunks
    results = client.query_points(
        collection_name=collection_name,
        query=question_embedding,
        limit=top_k
    )

    # Return only the text content of matching chunks
    return [result.payload["text"] for result in results.points]