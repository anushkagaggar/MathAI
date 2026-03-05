import os
from dotenv import load_dotenv
from langchain_core.documents import Document
from utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Use /data/memory on HF Spaces for persistence, else local
_hf_space = os.environ.get("SPACE_ID")
if _hf_space:
    MEMORY_INDEX_DIR = "/data/memory/memory_faiss_index"
else:
    MEMORY_INDEX_DIR = os.path.join(_project_root, "memory", "memory_faiss_index")

_memory_index = None


def _get_embedder():
    from rag.embedder import get_embedder
    return get_embedder()


def _get_or_create_memory_index():
    """
    Loads memory FAISS index if it exists.
    Returns None if no past problems have been saved yet.
    """
    global _memory_index

    if _memory_index is not None:
        return _memory_index

    index_file = os.path.join(MEMORY_INDEX_DIR, "index.faiss")
    if not os.path.exists(index_file):
        logger.debug("Memory FAISS index not yet created — no past problems")
        return None

    try:
        from langchain_community.vectorstores import FAISS
        _memory_index = FAISS.load_local(
            MEMORY_INDEX_DIR,
            _get_embedder(),
            allow_dangerous_deserialization=True
        )
        logger.info("Memory FAISS index loaded from %s", MEMORY_INDEX_DIR)
        return _memory_index
    except Exception as e:
        logger.error("Failed to load memory FAISS index: %s", str(e))
        return None


def add_to_memory_index(problem_text: str, problem_id: str) -> None:
    """
    Adds a new problem to the memory FAISS index.
    Creates the index if it doesn't exist yet.
    """
    global _memory_index

    from langchain_community.vectorstores import FAISS

    doc = Document(
        page_content=problem_text,
        metadata={"problem_id": problem_id, "source": "memory"}
    )

    os.makedirs(MEMORY_INDEX_DIR, exist_ok=True)

    try:
        if _memory_index is not None:
            _memory_index.add_documents([doc])
        else:
            index_file = os.path.join(MEMORY_INDEX_DIR, "index.faiss")
            if os.path.exists(index_file):
                _memory_index = FAISS.load_local(
                    MEMORY_INDEX_DIR,
                    _get_embedder(),
                    allow_dangerous_deserialization=True
                )
                _memory_index.add_documents([doc])
            else:
                _memory_index = FAISS.from_documents([doc], _get_embedder())

        _memory_index.save_local(MEMORY_INDEX_DIR)
        logger.info("Memory FAISS index updated with problem %s", problem_id)

    except Exception as e:
        logger.error("Failed to update memory FAISS index: %s", str(e))


def retrieve_similar(query: str, k: int = None) -> list:
    """
    Retrieves similar past problems from memory FAISS index.
    Only returns high-quality results (verifier_score >= 0.8).
    Returns [] if no memory exists yet.
    """
    if not query or not query.strip():
        return []

    if k is None:
        try:
            k = int(os.getenv("MEMORY_TOP_K", "3"))
        except ValueError:
            k = 3

    index = _get_or_create_memory_index()
    if index is None:
        logger.debug("No memory index available — skipping memory retrieval")
        return []

    try:
        results = index.similarity_search_with_score(query, k=k)
    except Exception as e:
        logger.error("Memory retrieval failed: %s", str(e))
        return []

    if not results:
        return []

    # Load full problem records from JSON store
    from memory.memory_store import load_all_problems
    all_problems = {p["id"]: p for p in load_all_problems()}

    output = []
    for doc, score in results:
        problem_id = doc.metadata.get("problem_id")
        relevance = max(0.0, round(1.0 - (score / 2.0), 3))

        record = all_problems.get(problem_id)
        if not record:
            logger.warning("Memory FAISS references unknown problem_id: %s", problem_id)
            continue

        # Only return high-quality past solutions
        verifier_score = record.get("verifier_score", 0.0)
        if verifier_score < 0.8:
            logger.debug("Skipping low-quality memory entry %s (score: %.2f)", problem_id, verifier_score)
            continue

        output.append({
            "problem_text": record.get("extracted_text", ""),
            "answer": record.get("final_answer", ""),
            "topic": record.get("topic", "unknown"),
            "verifier_score": verifier_score,
            "problem_id": problem_id,
            "relevance": relevance
        })

    logger.info("Memory retrieval: found %d high-quality similar problems", len(output))
    return output