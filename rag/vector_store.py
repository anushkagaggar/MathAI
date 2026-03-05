import os
import glob
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from utils.logger import get_logger
from rag.embedder import get_embedder
logger = get_logger(__name__)

load_dotenv()

KNOWLEDGE_BASE_DIR = os.path.join(os.path.dirname(__file__), "knowledge_base")
FAISS_INDEX_DIR = os.path.join(os.path.dirname(__file__), "faiss_index")


def _load_knowledge_base_docs() -> list[Document]:
    """
    Reads all .md and .txt files from knowledge_base/,
    splits into chunks, returns list of Document objects.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""]
    )

    all_docs = []
    files = glob.glob(os.path.join(KNOWLEDGE_BASE_DIR, "*.md")) + \
            glob.glob(os.path.join(KNOWLEDGE_BASE_DIR, "*.txt"))

    if not files:
        raise FileNotFoundError(f"No knowledge base files found in {KNOWLEDGE_BASE_DIR}")

    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        source_name = os.path.basename(filepath)
        chunks = splitter.split_text(content)

        for i, chunk in enumerate(chunks):
            all_docs.append(Document(
                page_content=chunk,
                metadata={"source": source_name, "chunk_index": i}
            ))
            logger.debug("Loaded %d chunks from %s", len(chunks), source_name)

    return all_docs


def build_vector_store() -> FAISS:
    """
    Builds FAISS index from knowledge base docs, saves to disk.
    Returns the FAISS index object.
    """
    logger.info("[RAG] Building FAISS vector store from knowledge base...")
    docs = _load_knowledge_base_docs()
    logger.info("Loaded %d total chunks from knowledge base", len(docs))
    embedder = get_embedder()
    faiss_index = FAISS.from_documents(documents=docs, embedding=embedder)

    os.makedirs(FAISS_INDEX_DIR, exist_ok=True)
    faiss_index.save_local(FAISS_INDEX_DIR)
    logger.info(f"[RAG] FAISS index saved to {FAISS_INDEX_DIR}")

    return faiss_index


def load_vector_store() -> FAISS:
    """
    Loads FAISS index from disk if it exists, otherwise builds it first.
    Returns the FAISS index object.
    """
    index_file = os.path.join(FAISS_INDEX_DIR, "index.faiss")

    if os.path.exists(index_file):
        embedder = get_embedder()
        faiss_index = FAISS.load_local(
            FAISS_INDEX_DIR,
            embedder,
            allow_dangerous_deserialization=True   # safe: index built from our own files
        )
        return faiss_index
    else:
        logger.warning("FAISS index not found — building from scratch")
        return build_vector_store()