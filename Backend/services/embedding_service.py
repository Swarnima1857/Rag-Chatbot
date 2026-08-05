import requests
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
import pypdf
import uuid
import re
import os
from dotenv import load_dotenv

# load .env file
load_dotenv()

# Qdrant Cloud connection details
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
OLLAMA_URL = os.getenv("OLLAMA_URL")

# Initialize Qdrant client
client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    check_compatibility=False
)



# STEP 1 — EXTRACT TEXT FROM PDF

def extract_text_from_pdf(pdf_path: str):
    """
    Extract all text content from a PDF file.
    Cleans extra whitespace and joins pages with double newlines
    to preserve paragraph structure.
    """
    reader = pypdf.PdfReader(pdf_path)
    pages_text = []

    for page_num, page in enumerate(reader.pages):
        extracted = page.extract_text()
        if extracted:
            cleaned = extracted.strip()
            pages_text.append(cleaned)

    # Join all pages with double newline to preserve paragraph boundaries
    full_text = "\n\n".join(pages_text)
    return full_text


# STEP 2 — SEMANTIC CHUNKING

def semantic_chunking(
    text: str,
    max_chunk_size: int = 500,
    min_chunk_size: int = 100,
    overlap_sentences: int = 1
):
    """
    Splits text into meaningful semantic chunks based on paragraph
    and sentence boundaries — not just fixed character counts.

    Strategy:
    1. Split text into paragraphs using double newlines
    2. If a paragraph is too large, split it further by sentences
    3. Merge small paragraphs together up to max_chunk_size
    4. Carry forward the last sentence as overlap between chunks
    """

    chunks = []

    # Split text into paragraphs using double newlines as boundary
    paragraphs = re.split(r'\n\n+', text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    current_chunk = ""
    last_sentence = ""  # Used for overlap between chunks

    for para in paragraphs:

        # Case 1: Paragraph is too large — split it by sentences
        if len(para) > max_chunk_size:

            # Save the current chunk before processing large paragraph
            if current_chunk.strip() and len(current_chunk) >= min_chunk_size:
                chunks.append(current_chunk.strip())
                # Carry last sentence forward as overlap
                sentences = current_chunk.split('. ')
                last_sentence = sentences[-1] if sentences else ""

            # Split large paragraph into individual sentences
            sentences = re.split(r'(?<=[.!?])\s+', para)
            sentences = [s.strip() for s in sentences if s.strip()]

            # Start new chunk with overlap from previous chunk
            temp_chunk = last_sentence + " " if last_sentence else ""

            for sentence in sentences:
                # If adding this sentence exceeds max size — save current chunk
                if len(temp_chunk) + len(sentence) > max_chunk_size:
                    if temp_chunk.strip() and len(temp_chunk) >= min_chunk_size:
                        chunks.append(temp_chunk.strip())
                        # Carry this sentence as overlap into next chunk
                        last_sentence = sentence
                        temp_chunk = sentence + " "
                    else:
                        # Chunk too small — keep adding sentences
                        temp_chunk += sentence + " "
                else:
                    temp_chunk += sentence + " "

            # Whatever is left goes into current_chunk
            current_chunk = temp_chunk

        # Case 2: Paragraph fits — merge it into current chunk
        elif len(current_chunk) + len(para) <= max_chunk_size:
            current_chunk += "\n\n" + para if current_chunk else para

        # Case 3: Current chunk is full — save it and start new one
        else:
            if current_chunk.strip() and len(current_chunk) >= min_chunk_size:
                chunks.append(current_chunk.strip())
                # Carry last sentence as overlap
                sentences = current_chunk.split('. ')
                last_sentence = sentences[-1] if len(sentences) > 1 else ""

            # Start new chunk with overlap + current paragraph
            current_chunk = last_sentence + " " + para if last_sentence else para

    # Save the final remaining chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


# STEP 3 — CONVERT TEXT TO EMBEDDING USING OLLAMA
def get_embedding(text: str):
    """
    Sends text to Ollama's nomic-embed-text model and returns
    a 768-dimensional vector (embedding) representing the text.
    """
    response = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": "nomic-embed-text", "prompt": text}
    )
    return response.json()["embedding"]


# STEP 4 — PROCESS PDF (MAIN PIPELINE FUNCTION)

def process_pdf(pdf_path: str, session_id: str):
    """
    Complete RAG ingestion pipeline:
    PDF → Extract Text → Semantic Chunks → Embeddings → Qdrant

    Args:
        pdf_path   : Path to the uploaded PDF file
        session_id : Unique session ID to store chunks under
    Returns:
        Number of chunks created and stored
    """
    collection_name = f"session_{session_id}"

    # Step 1 — Extract text from PDF
    print(f"\n[PROCESSING] PDF: {pdf_path}")
    text = extract_text_from_pdf(pdf_path)

    if not text.strip():
        raise ValueError("No text found in the PDF!")

    print(f"[TEXT LENGTH] {len(text)} characters extracted")

    # Step 2 — Create semantic chunks
    chunks = semantic_chunking(text)
    print(f"[CHUNKS] {len(chunks)} semantic chunks created")

    # Log chunk size distribution for debugging
    sizes = [len(c) for c in chunks]
    print(f"[CHUNK SIZES] Min: {min(sizes)}, Max: {max(sizes)}, Avg: {sum(sizes)//len(sizes)}")

    # Step 3 — Create a fresh Qdrant collection for this session
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
                payload={
                    "text": chunk,
                    "chunk_index": i,
                    "source": pdf_path,       # Track which PDF this chunk came from
                    "chunk_size": len(chunk)  # Track chunk size for debugging
                }
            )
        )

    # Step 5 — Store all points in Qdrant
    client.upsert(collection_name=collection_name, points=points)
    print(f"[SAVED] {len(chunks)} chunks saved to Qdrant")

    return len(chunks)





# STEP 5 — SEARCH RELEVANT CHUNKS WITH DEBUG LOGGING

def search_similar_chunks(question: str, session_id: str, top_k: int = 3):
    """
    Finds the most semantically similar chunks for a given question.
    Logs query, retrieved chunks, and similarity scores for debugging.

    Args:
        question   : User's question
        session_id : Session to search within
        top_k      : Number of top chunks to retrieve (default: 3)
    Returns:
        List of relevant text chunks
    """
    collection_name = f"session_{session_id}"

    # Convert question to embedding
    question_embedding = get_embedding(question)

    # Search Qdrant for most similar chunks
    results = client.query_points(
        collection_name=collection_name,
        query=question_embedding,
        limit=top_k,
        with_payload=True
    )

    # ── DEBUG LOGGING (Assignment Requirement) ──
    print(f"\n{'='*50}")
    print(f"[QUERY]  : {question}")
    print(f"[TOP {top_k} CHUNKS RETRIEVED]:")

    chunks_with_scores = []
    for i, result in enumerate(results.points):
        print(f"\n  Chunk {i+1}:")
        print(f"  Source : {result.payload.get('source', 'Unknown')}")
        print(f"  Score  : {result.score:.4f}")
        print(f"  Text   : {result.payload['text'][:150]}...")

        chunks_with_scores.append({
            "text": result.payload["text"],
            "score": result.score,
            "source": result.payload.get("source", "Unknown")
        })

    print(f"{'='*50}\n")

    # Return only text content for chat.py
    return [c["text"] for c in chunks_with_scores]



def load_company_documents(docs_folder: str = "company_docs"):
    """
    Loads all PDF documents from company_docs folder
    and stores them in a single Qdrant collection.
    This runs once when the server starts.
    """
    collection_name = "company_knowledge_base"
    
    if not os.path.exists(docs_folder):
        print(f"[ERROR] Folder '{docs_folder}' not found!")
        return 0
    
    pdf_files = [
        f for f in os.listdir(docs_folder) 
        if f.endswith('.pdf')
    ]
    
    if not pdf_files:
        print(f"[WARNING] No PDFs found in '{docs_folder}'!")
        return 0
    
    print(f"\n[LOADING] Found {len(pdf_files)} PDFs to process...")
    
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=768, distance=Distance.COSINE)
    )
    
    total_chunks = 0
    all_points = []
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(docs_folder, pdf_file)
        print(f"\n[PROCESSING] {pdf_file}...")
        
        text = extract_text_from_pdf(pdf_path)
        if not text.strip():
            print(f"[SKIP] No text found in {pdf_file}")
            continue
        
        chunks = semantic_chunking(text)
        print(f"[CHUNKS] {len(chunks)} chunks created from {pdf_file}")
        
        for i, chunk in enumerate(chunks):
            embedding = get_embedding(chunk)
            all_points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={
                        "text": chunk,
                        "source": pdf_file,
                        "chunk_index": i,
                        "chunk_size": len(chunk)
                    }
                )
            )
        
        total_chunks += len(chunks)
    
    if all_points:
        client.upsert(
            collection_name=collection_name,
            points=all_points
        )
    
    print(f"\n[DONE] {total_chunks} total chunks saved from {len(pdf_files)} PDFs!")
    return total_chunks


def search_company_docs(question: str, top_k: int = 3):
    """
    Search in company knowledge base — no session needed!
    """
    collection_name = "company_knowledge_base"
    
    question_embedding = get_embedding(question)
    
    results = client.query_points(
        collection_name=collection_name,
        query=question_embedding,
        limit=top_k,
        with_payload=True
    )
    
    print(f"\n{'='*50}")
    print(f"[QUERY]  : {question}")
    print(f"[TOP {top_k} CHUNKS RETRIEVED]:")
    
    chunks_with_scores = []
    for i, result in enumerate(results.points):
        print(f"\n  Chunk {i+1}:")
        print(f"  Source : {result.payload.get('source', 'Unknown')}")
        print(f"  Score  : {result.score:.4f}")
        print(f"  Text   : {result.payload['text'][:150]}...")
        
        chunks_with_scores.append({
            "text": result.payload["text"],
            "score": result.score,
            "source": result.payload.get("source", "Unknown")
        })
    
    print(f"{'='*50}\n")
    
    return chunks_with_scores
