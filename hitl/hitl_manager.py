from utils.logger import get_logger

logger = get_logger(__name__)


def get_hitl_context(state: dict) -> dict:
    """
    Returns a summary dict of why HITL was triggered and what needs review.
    Used by the UI to render the appropriate HITL panel.
    """
    # Determine which agent triggered HITL
    trace = state.get("agent_trace", [])
    trigger_agent = "Unknown"
    for entry in reversed(trace):
        if entry.get("action") in ("fallback", "error", "routed"):
            trigger_agent = entry.get("agent", "Unknown")
            break

    # Detect trigger type from context
    confidence = state.get("confidence", 1.0)
    input_type = state.get("input_type", "text")
    verifier_score = state.get("verifier_score", None)

    if verifier_score is not None and verifier_score < float(__import__('os').getenv("VERIFIER_CONFIDENCE_THRESHOLD", "0.80")):
        trigger_type = "verifier"
    elif confidence < 0.75 and input_type == "image":
        trigger_type = "ocr"
    elif confidence < 0.75 and input_type == "audio":
        trigger_type = "asr"
    else:
        trigger_type = "parser"

    return {
        "reason": state.get("hitl_reason", "Human review required."),
        "trigger_agent": trigger_agent,
        "trigger_type": trigger_type,
        "current_text": state.get("extracted_text", ""),
        "current_answer": state.get("solver_output", ""),
        "confidence": confidence,
        "verifier_score": verifier_score,
        "verifier_notes": state.get("verifier_notes", "")
    }


def apply_human_decision(state: dict, decision: str,
                          edited_text: str = None,
                          comment: str = None) -> dict:
    """
    Applies a human reviewer's decision to the pipeline state.

    decision: 'approve' | 'edit' | 'reject'
    edited_text: corrected text (for 'edit' decision)
    comment: optional reviewer comment (for 'reject' or 'edit')

    Returns updated state dict.
    """
    problem_id = state.get("last_problem_id", "unknown")
    hitl_context = get_hitl_context(state)
    trigger_type = hitl_context.get("trigger_type", "unknown")

    if decision == "approve":
        state["needs_hitl"] = False
        state["hitl_approved"] = True
        logger.info("HITL approved by human. Trigger: %s | Problem: %s", trigger_type, problem_id)

        state.setdefault("agent_trace", []).append({
            "agent": "HITL",
            "action": "approved",
            "output": f"Human approved. Trigger: {trigger_type}"
        })

    elif decision == "edit":
        if edited_text:
            original_text = state.get("extracted_text", "")

            # Apply edit based on trigger type
            if trigger_type in ("ocr", "asr", "parser"):
                state["extracted_text"] = edited_text
                state["human_edited_text"] = edited_text
                logger.info("HITL edit applied to extracted_text. Problem: %s", problem_id)

                # Save correction to memory for learning
                try:
                    from memory.memory_store import save_correction
                    save_correction(
                        original=original_text,
                        corrected=edited_text,
                        problem_id=problem_id
                    )
                except Exception as e:
                    logger.warning("Failed to save HITL correction: %s", str(e))

            elif trigger_type == "verifier":
                state["solver_output"] = edited_text
                state["human_edited_text"] = edited_text
                logger.info("HITL edit applied to solver_output. Problem: %s", problem_id)

        state["needs_hitl"] = False
        state["hitl_approved"] = True

        state.setdefault("agent_trace", []).append({
            "agent": "HITL",
            "action": "edited",
            "output": f"Human edited {trigger_type} output. Comment: {comment or 'none'}"
        })

    elif decision == "reject":
        state["workflow_route"] = "reject"
        state["needs_hitl"] = False
        state["hitl_approved"] = False
        logger.info("HITL rejected by human. Trigger: %s | Comment: %s | Problem: %s",
                    trigger_type, comment or "none", problem_id)

        # Save rejection to memory
        try:
            from memory.memory_store import save_correction
            save_correction(
                original=state.get("extracted_text", ""),
                corrected="[REJECTED]",
                problem_id=problem_id
            )
        except Exception as e:
            logger.warning("Failed to save HITL rejection: %s", str(e))

        state.setdefault("agent_trace", []).append({
            "agent": "HITL",
            "action": "rejected",
            "output": f"Human rejected. Comment: {comment or 'none'}"
        })

    else:
        logger.warning("apply_human_decision: unknown decision '%s'", decision)

    return state