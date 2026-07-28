import requests
from qdrant_client import QdrantClient
from rank_bm25 import BM25Okapi
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
    Loads all PDF documents from company_docs folder and builds both:
    1. Qdrant vector index (semantic search)
    2. BM25 keyword index (exact keyword search)
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
    all_chunks_text = [] # store chunks for BM25
    
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
            # Store Text for BM25
            all_chunks_text.append({"text": chunk, "source": pdf_file})
        
        total_chunks += len(chunks)
    
    if all_points:
        client.upsert(
            collection_name=collection_name,
            points=all_points
        )
    # Build BM25 index
    build_bm25_index([c["text"] for c in all_chunks_text])
 
    # save Source info globally
    global bm25_chunks
    bm25_chunks = all_chunks_text
    
    print(f"\n[DONE] {total_chunks} total chunks saved from {len(pdf_files)} PDFs!")
    return total_chunks
 
    # Global BM25 index - for keyword search
# Global BM25 index - for keyword search
bm25_index = None
bm25_chunks = []  # Store chunk's text
 
 
def build_bm25_index(chunks_text: list):
    """
    Build BM25 keyword search index from all chunks.
    This allows exact keyword matching alongside vector search.
    """
    global bm25_index, bm25_chunks
 
    # store chunks for retrieval later
    bm25_chunks = chunks_text
 
    # Tokenize - break chunks in words
    tokenized_chunks = [chunk.lower().split() for chunk in chunks_text]
 
    # Build BM25 index
    bm25_index = BM25Okapi(tokenized_chunks)
 
    print(f"[BM25] Index built with {len(chunks_text)} chunks")
 
 
def hybrid_search(question: str, top_k: int = 3):
    """Hybrid Search = BM25 (keyword) + Vector (semantic) + Re Ranking
    step 1: Vector search from Qdrant
    step 2: BM25 keyword search
    step 3: Combine scores and re-rank results
    step 4: Return top_k best chunks
    """
 
    # Vector Search
    print(f"\n[VECTOR SEARCH] SEARCHING QDRANT...")
    question_embedding = get_embedding(question)
 
    vector_results = client.query_points(
        collection_name="company_knowledge_base",
        query=question_embedding,
        limit=10,
        with_payload=True
    )
 
    # store vector results in dict
    vector_scores = {}
    for result in vector_results.points:
        text = result.payload["text"]
        vector_scores[text] = {
            "score": result.score,
            "source": result.payload.get("source", "Unknown"),
            "text": text
        }
 
    # ── Step 2: Search BM25 Keywords ──
    print(f"[BM25 SEARCH] Searching keywords...")
 
    if bm25_index is None:
        print("[WARNING] BM25 index not built yet!")
        bm25_results = []
    else:
        # tokenize question
        tokenized_question = question.lower().split()
 
        # retrieve BM25 scores
        bm25_scores = bm25_index.get_scores(tokenized_question)
 
        # retrieve top 10 BM25 results
        top_bm25_indices = sorted(
            range(len(bm25_scores)),
            key=lambda i: bm25_scores[i],
            reverse=True
        )[:10]
 
        bm25_results = []
        for idx in top_bm25_indices:
            if bm25_scores[idx] > 0:
                bm25_results.append({
                    "text": bm25_chunks[idx]["text"],
                    "source": bm25_chunks[idx]["source"],
                    "bm25_score": bm25_scores[idx]
                })
 
    # ── Step 3: Re-ranking — combine both scores ──
    print(f"[RE-RANKING] Combining vector + BM25 scores...")
 
    combined_scores = {}
 
    # add Vector scores (normalize 0-1)
    for text, data in vector_scores.items():
        if text not in combined_scores:
            combined_scores[text] = {
                "text": text,
                "source": data["source"],
                "vector_score": 0,
                "bm25_score": 0,
                "combined_score": 0
            }
 
        combined_scores[text]["bm25_score"] = normalized_bm25
 
    # Calculate combined score
    for text in combined_scores:
        v_score = combined_scores[text]["vector_score"]
        b_score = combined_scores[text]["bm25_score"]
        combined_scores[text]["combined_score"] = (0.6 * v_score) + (0.4 * b_score)
 
    # ── Step 4: Sort by combined score ──
    ranked_results = sorted(
        combined_scores.values(),
        key=lambda x: x["combined_score"],
        reverse=True
    )[:top_k]
 
    # ── Debug Logging ──
    print(f"\n{'='*60}")
    print(f"[QUERY]  : {question}")
    print(f"[HYBRID SEARCH RESULTS — TOP {top_k}]:")
 
    for i, result in enumerate(ranked_results):
        print(f"\n  Chunk {i+1}:")
        print(f"  Source        : {result['source']}")
        print(f"  Vector Score  : {result['vector_score']:.4f}")
        print(f"  BM25 Score    : {result['bm25_score']:.4f}")
        print(f"  Combined Score: {result['combined_score']:.4f}")
        print(f"  Text          : {result['text'][:150]}...")
 
    print(f"{'='*60}\n")
 
    return ranked_results
 
 
def search_company_docs(question: str, top_k: int = 3):
    """
    Search company documents using Hybrid Search.
    Combines vector search + BM25 keyword search + re-ranking.
    """
    # use Hybrid Search
    results = hybrid_search(question, top_k=top_k)
    return results
  
def search_company_docs(question: str, top_k: int = 3):
    """
    Search company documents using Hybrid Search.
    Combines vector search + BM25 keyword search + re-ranking.
    """
    # use Hybrid  Search
    results = hybrid_search(question, top_k=top_k)
    return results
 