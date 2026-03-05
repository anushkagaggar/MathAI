import os
import json
import uuid
import tempfile
import shutil
from datetime import datetime, timezone
from dotenv import load_dotenv
from utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)


class _NumpySafeEncoder(json.JSONEncoder):
    """
    JSON encoder that converts numpy scalar types to native Python types.
    FAISS returns numpy float32/int64 — standard json.dump() chokes on these.
    """
    def default(self, obj):
        try:
            import numpy as np
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, np.integer):
                return int(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
        except ImportError:
            pass
        return super().default(obj)

MEMORY_FILE_PATH = os.getenv("MEMORY_FILE_PATH", "memory/solved_problems.json")

# Resolve to absolute path relative to project root
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Allow override for HF Spaces persistent storage
_hf_space = os.environ.get("SPACE_ID")
if _hf_space:
    _memory_dir = "/data/memory"
    os.makedirs(_memory_dir, exist_ok=True)
    MEMORY_FILE = os.path.join(_memory_dir, "solved_problems.json")
else:
    MEMORY_FILE = os.path.join(_project_root, MEMORY_FILE_PATH)
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)


def _load_file() -> list:
    """Load all records from JSON file. Returns empty list if file missing."""
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Failed to load memory file: %s", str(e))
        return []


def _write_file(records: list) -> None:
    """
    Atomically write records to JSON file.
    Uses temp file + rename to prevent corruption on crash.
    """
    dir_path = os.path.dirname(MEMORY_FILE)
    os.makedirs(dir_path, exist_ok=True)

    try:
        fd, tmp_path = tempfile.mkstemp(dir=dir_path, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False, cls=_NumpySafeEncoder)
        shutil.move(tmp_path, MEMORY_FILE)
    except OSError as e:
        logger.error("Failed to write memory file: %s", str(e))
        # Clean up temp file if it exists
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def save_problem(state: dict) -> str:
    """
    Saves a solved problem to JSON memory.
    Returns the generated problem_id.
    """
    problem_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now(timezone.utc).isoformat()

    # Extract sources only from retrieved_context (not full content) to save space
    context_sources = []
    for chunk in state.get("retrieved_context", []):
        context_sources.append({
            "source": chunk.get("source", "unknown"),
            "relevance": chunk.get("relevance", 0.0)
        })

    record = {
        "id": problem_id,
        "timestamp": timestamp,
        "input_type": state.get("input_type", "text"),
        "extracted_text": state.get("extracted_text", ""),
        "parsed_problem": state.get("parsed_problem", {}),
        "topic": state.get("topic", "unknown"),
        "context_sources": context_sources,
        "solver_output": state.get("solver_output", ""),
        "sympy_result": state.get("sympy_result", ""),
        "verifier_score": state.get("verifier_score", 0.0),
        "verifier_notes": state.get("verifier_notes", ""),
        "final_answer": state.get("final_answer", ""),
        "explanation": state.get("explanation", ""),
        "user_feedback": "",
        "user_comment": "",
        "type": "solved"
    }

    records = _load_file()
    records.append(record)
    _write_file(records)

    logger.info("Saved problem %s to memory (topic: %s)", problem_id, record["topic"])

    # Update memory FAISS index
    try:
        from memory.memory_retriever import add_to_memory_index
        problem_text = state.get("parsed_problem", {}).get("problem_text", state.get("extracted_text", ""))
        if problem_text:
            add_to_memory_index(problem_text, problem_id)
    except Exception as e:
        logger.warning("Failed to update memory FAISS index: %s", str(e))

    return problem_id


def save_feedback(problem_id: str, feedback: str, comment: str = "") -> None:
    """Updates user_feedback and user_comment on an existing record."""
    records = _load_file()
    updated = False

    for record in records:
        if record.get("id") == problem_id:
            record["user_feedback"] = feedback
            record["user_comment"] = comment
            updated = True
            break

    if updated:
        _write_file(records)
        logger.info("Feedback saved for problem %s: %s", problem_id, feedback)
    else:
        logger.warning("save_feedback: problem_id %s not found", problem_id)


def save_correction(original: str, corrected: str, problem_id: str) -> None:
    """Saves a HITL correction record for learning OCR/ASR patterns."""
    record = {
        "id": str(uuid.uuid4())[:8],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": "correction",
        "original": original,
        "corrected": corrected,
        "parent_problem_id": problem_id
    }
    records = _load_file()
    records.append(record)
    _write_file(records)
    logger.info("Correction saved for problem %s", problem_id)


def load_all_problems() -> list:
    """Returns all records from JSON memory. Empty list if none."""
    return _load_file()


def get_problem_by_id(problem_id: str) -> dict:
    """Returns a single problem record by id. None if not found."""
    for record in _load_file():
        if record.get("id") == problem_id:
            return record
    return None