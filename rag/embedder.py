import os
from dotenv import load_dotenv

load_dotenv()

# Singleton pattern — model loaded once at module level
_embedder = None


def get_embedder():
    """
    Returns the singleton HuggingFace embedding model.
    Downloads ~80MB to ~/.cache/huggingface/ on first call.
    Subsequent calls use cached model.
    """
    global _embedder

    if _embedder is None:
        from langchain_community.embeddings import HuggingFaceEmbeddings

        model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

        _embedder = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )

    return _embedder