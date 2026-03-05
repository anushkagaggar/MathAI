import os
from dotenv import load_dotenv
from utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

# Singleton — model loaded once at module level
_embedder = None


def get_embedder():
    """
    Returns the singleton HuggingFace embedding model.
    Downloads ~80MB to ~/.cache/huggingface/ on first call.
    Subsequent calls use cached model.
    """
    global _embedder

    if _embedder is None:
        logger.info("Loading embedding model — first run may download ~80MB...")
        try:
            # Use langchain-huggingface to avoid deprecation warning
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError:
            # Fallback to langchain-community if langchain-huggingface not installed
            logger.warning("langchain-huggingface not found, falling back to langchain-community")
            from langchain_community.embeddings import HuggingFaceEmbeddings

        model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

        _embedder = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
        logger.info("Embedding model loaded: %s", model_name)

    return _embedder