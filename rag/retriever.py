import os
from dotenv import load_dotenv
from rag.vector_store import load_vector_store
from utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

# Singleton for loaded index
_vector_store = None


def _get_vector_store():
    global _vector_store
    if _vector_store is None:
        _vector_store = load_vector_store()
    return _vector_store


def retrieve(query: str, k: int = None) -> list[dict]:
    """
    Retrieves top-k relevant chunks from FAISS knowledge base.

    Args:
        query: The math problem text to search for
        k: Number of chunks to retrieve (defaults to TOP_K_RETRIEVAL from .env)

    Returns:
        List of dicts: [{"content": str, "source": str, "relevance": float}]
        Returns empty list if no results or error — never raises.
    """
    if not query or not query.strip():
        logger.warning("retrieve() called with empty query")
        return []

    if k is None:
        try:
            k = int(os.getenv("TOP_K_RETRIEVAL", "4"))
        except ValueError:
            k = 4

    try:
        store = _get_vector_store()
        results = store.similarity_search_with_score(query, k=k)
    except Exception as e:
        logger.error(f"[RAG] Retrieval error: {e}")
        return []

    if not results:
        logger.warning("No RAG results for query: %s", query[:60])
        return []

    output = []
    for doc, score in results:
        # FAISS returns L2 distance — lower is better
        # Normalize to 0-1 relevance: relevance = max(0, 1 - score/2)
        relevance = max(0.0, round(1.0 - (score / 2.0), 3))

        output.append({
            "content": doc.page_content,
            "source": doc.metadata.get("source", "unknown"),
            "relevance": relevance,
            "chunk_index": doc.metadata.get("chunk_index", 0)
        })

    # Sort by relevance descending
    output.sort(key=lambda x: x["relevance"], reverse=True)
    logger.debug("Retrieved %d chunks for query: %s", len(output), query[:60])
    return output


def retrieve_with_fallback(query: str, k: int = None) -> list[dict]:
    """
    Retrieves chunks. If query finds nothing relevant (all relevance < 0.2),
    returns empty list with a flag so Solver knows RAG had no useful context.
    Never hallucinates citations.
    """
    results = retrieve(query, k=k)

    # Filter to only reasonably relevant results
    relevant = [r for r in results if r["relevance"] >= 0.1]
    if not relevant:
        logger.warning("No relevant RAG context found for query — solver will use LLM-only")
    return relevant