from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

# Ollama embedding model setup
embeddings = OllamaEmbeddings(model="nomic-embed-text")

# where ChromaDB will be save
CHROMA_DIR = "chroma_db"


def process_pdf(pdf_path: str, session_id: str):
    # Step 1 — load pdf
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    # Step 2 — devide in chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_documents(documents)

    # Step 3 — Save in ChromaDb (session-wise in seperate collection)
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
        collection_name=f"session_{session_id}"
    )

    return len(chunks)


def get_vectorstore(session_id: str):
    # load data from processed pdf
    vectorstore = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
        collection_name=f"session_{session_id}"
    )
    return vectorstore