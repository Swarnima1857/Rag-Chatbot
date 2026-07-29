import requests
from qdrant_client import QdrantClient
from rank_bm25 import BM25Okapi
from qdrant_client.models import PointStruct, VectorParams, Distance
import pypdf
import uuid
import re
import os
from dotenv import load_dotenv

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
OLLAMA_URL = os.getenv("OLLAMA_URL")

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    check_compatibility=False
)

# Global BM25 variables — must be at top level!
bm25_index = None
bm25_chunks = []


# STEP 1 — EXTRACT TEXT FROM PDF
def extract_text_from_pdf(pdf_path: str):
    reader = pypdf.PdfReader(pdf_path)
    pages_text = []
    for page_num, page in enumerate(reader.pages):
        extracted = page.extract_text()
        if extracted:
            pages_text.append(extracted.strip())
    return "\n\n".join(pages_text)


# STEP 2 — SEMANTIC CHUNKING
def semantic_chunking(text: str, max_chunk_size: int = 500, min_chunk_size: int = 100, overlap_sentences: int = 1):
    chunks = []
    paragraphs = re.split(r'\n\n+', text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    current_chunk = ""
    last_sentence = ""

    for para in paragraphs:
        if len(para) > max_chunk_size:
            if current_chunk.strip() and len(current_chunk) >= min_chunk_size:
                chunks.append(current_chunk.strip())
                sentences = current_chunk.split('. ')
                last_sentence = sentences[-1] if sentences else ""
            sentences = re.split(r'(?<=[.!?])\s+', para)
            sentences = [s.strip() for s in sentences if s.strip()]
            temp_chunk = last_sentence + " " if last_sentence else ""
            for sentence in sentences:
                if len(temp_chunk) + len(sentence) > max_chunk_size:
                    if temp_chunk.strip() and len(temp_chunk) >= min_chunk_size:
                        chunks.append(temp_chunk.strip())
                        last_sentence = sentence
                        temp_chunk = sentence + " "
                    else:
                        temp_chunk += sentence + " "
                else:
                    temp_chunk += sentence + " "
            current_chunk = temp_chunk
        elif len(current_chunk) + len(para) <= max_chunk_size:
            current_chunk += "\n\n" + para if current_chunk else para
        else:
            if current_chunk.strip() and len(current_chunk) >= min_chunk_size:
                chunks.append(current_chunk.strip())
                sentences = current_chunk.split('. ')
                last_sentence = sentences[-1] if len(sentences) > 1 else ""
            current_chunk = last_sentence + " " + para if last_sentence else para

    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    return chunks


# STEP 3 — GET EMBEDDING FROM OLLAMA
def get_embedding(text: str):
    response = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": "nomic-embed-text", "prompt": text}
    )
    return response.json()["embedding"]


# STEP 4 — BUILD BM25 INDEX
def build_bm25_index(chunks_data: list):
    """
    Build BM25 keyword index from chunk texts.
    chunks_data = list of strings
    """
    global bm25_index, bm25_chunks
    tokenized_chunks = [chunk.lower().split() for chunk in chunks_data]
    bm25_index = BM25Okapi(tokenized_chunks)
    print(f"[BM25] Index built with {len(chunks_data)} chunks")


# STEP 5 — LOAD COMPANY DOCUMENTS
def load_company_documents(docs_folder: str = "company_docs"):
    """
    Load all PDFs and build Qdrant + BM25 indexes.
    Runs once at server startup.
    """
    global bm25_chunks
    collection_name = "company_knowledge_base"

    if not os.path.exists(docs_folder):
        print(f"[ERROR] Folder '{docs_folder}' not found!")
        return 0

    pdf_files = [f for f in os.listdir(docs_folder) if f.endswith('.pdf')]

    if not pdf_files:
        print(f"[WARNING] No PDFs found!")
        return 0

    print(f"\n[LOADING] Found {len(pdf_files)} PDFs to process...")

    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=768, distance=Distance.COSINE)
    )

    total_chunks = 0
    all_points = []
    all_chunks_data = []

    for pdf_file in pdf_files:
        pdf_path = os.path.join(docs_folder, pdf_file)
        print(f"\n[PROCESSING] {pdf_file}...")

        text = extract_text_from_pdf(pdf_path)
        if not text.strip():
            print(f"[SKIP] No text in {pdf_file}")
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
            all_chunks_data.append({
                "text": chunk,
                "source": pdf_file
            })

        total_chunks += len(chunks)

    if all_points:
        client.upsert(collection_name=collection_name, points=all_points)

    # Build BM25 index
    build_bm25_index([c["text"] for c in all_chunks_data])

    # Save source info globally
    bm25_chunks = all_chunks_data

    print(f"\n[DONE] {total_chunks} total chunks saved from {len(pdf_files)} PDFs!")
    return total_chunks


# STEP 6 — HYBRID SEARCH
def hybrid_search(question: str, top_k: int = 3):
    """
    Hybrid Search = Vector Search + BM25 + Re-ranking
    """

    # Step 1 — Vector Search
    print(f"\n[VECTOR SEARCH] Searching Qdrant...")
    question_embedding = get_embedding(question)

    vector_results = client.query_points(
        collection_name="company_knowledge_base",
        query=question_embedding,
        limit=10,
        with_payload=True
    )

    vector_scores = {}
    for result in vector_results.points:
        text = result.payload["text"]
        vector_scores[text] = {
            "score": result.score,
            "source": result.payload.get("source", "Unknown"),
            "text": text
        }

    # Step 2 — BM25 Keyword Search
    print(f"[BM25 SEARCH] Searching keywords...")

    bm25_results = []
    if bm25_index is None:
        print("[WARNING] BM25 index not built!")
    else:
        tokenized_question = question.lower().split()
        scores = bm25_index.get_scores(tokenized_question)

        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:10]

        for idx in top_indices:
            if scores[idx] > 0:
                bm25_results.append({
                    "text": bm25_chunks[idx]["text"],
                    "source": bm25_chunks[idx]["source"],
                    "bm25_score": scores[idx]
                })

    # Step 3 — Re-ranking: Combine Scores
    print(f"[RE-RANKING] Combining vector + BM25 scores...")

    combined_scores = {}

    # Add vector scores
    for text, data in vector_scores.items():
        combined_scores[text] = {
            "text": text,
            "source": data["source"],
            "vector_score": data["score"],  # ← sahi jagah score add kiya!
            "bm25_score": 0.0,
            "combined_score": 0.0
        }

    # Add BM25 scores (normalized 0-1)
    max_bm25 = max([r["bm25_score"] for r in bm25_results], default=1)
    for result in bm25_results:
        text = result["text"]
        norm_score = result["bm25_score"] / max_bm25  # ← normalized_bm25 fix!
        if text in combined_scores:
            combined_scores[text]["bm25_score"] = norm_score
        else:
            combined_scores[text] = {
                "text": text,
                "source": result["source"],
                "vector_score": 0.0,
                "bm25_score": norm_score,
                "combined_score": 0.0
            }

    # Calculate final combined score: 60% vector + 40% BM25
    for text in combined_scores:
        v = combined_scores[text]["vector_score"]
        b = combined_scores[text]["bm25_score"]
        combined_scores[text]["combined_score"] = (0.6 * v) + (0.4 * b)

    # Step 4 — Sort and return top_k
    ranked = sorted(
        combined_scores.values(),
        key=lambda x: x["combined_score"],
        reverse=True
    )[:top_k]

    # Debug Logging
    print(f"\n{'='*60}")
    print(f"[QUERY]         : {question}")
    print(f"[TOP {top_k} RESULTS]:")
    for i, r in enumerate(ranked):
        print(f"\n  Chunk {i+1}:")
        print(f"  Source         : {r['source']}")
        print(f"  Vector Score   : {r['vector_score']:.4f}")
        print(f"  BM25 Score     : {r['bm25_score']:.4f}")
        print(f"  Combined Score : {r['combined_score']:.4f}")
        print(f"  Text           : {r['text'][:100]}...")
    print(f"{'='*60}\n")

    return ranked


# STEP 7 — SEARCH COMPANY DOCS
def search_company_docs(question: str, top_k: int = 3):
    """
    Main search function — uses hybrid search.
    """
    return hybrid_search(question, top_k=top_k)