"""api.routes.patient_eval

Patient evaluation endpoint:
  POST /api/v1/eval/patient — run DeepEval metrics on a session's conversation
"""

from __future__ import annotations

import os
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.utils.logger import get_logger

logger = get_logger(__name__)

from api.dependencies import get_patient_evaluator
from api.models import PatientEvalRequest, PatientEvalResponse
from api.database import get_session_info, get_session_history, save_evaluation
from src.evaluation.patient.interfaces import PatientEvalConfig
from src.evaluation.patient.deepeval_patient import DeepEvalPatientEvaluator

router = APIRouter(prefix="/eval", tags=["Evaluation"])


def _is_conversation_ready(history: list, min_turns: int = 2) -> bool:
    non_system = [m for m in history if m.get("role") != "system"]
    return len(non_system) >= min_turns


@router.post("/patient", response_model=PatientEvalResponse)
def evaluate_patient(
    body: PatientEvalRequest,
    evaluator: Annotated[DeepEvalPatientEvaluator, Depends(get_patient_evaluator)],
) -> PatientEvalResponse:
    """
    Evaluate the simulated patient's performance using DeepEval metrics.

    Requires at least one trainee message and one patient reply in the session.
    Requires `OPENAI_API_KEY` to be configured (DeepEval uses OpenAI as judge).
    """
    logger.info(f"Patient evaluation triggered: session_id={body.session_id!r}")
    
    if not getattr(evaluator, "available", True):
        logger.error("DeepEval is not available")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DeepEval is not installed. Install with: pip install -U deepeval",
        )

    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENAI_API_KEY is not configured on the server.",
        )

    session = get_session_info(body.session_id)
    if session is None:
        logger.warning(f"Session not found: {body.session_id!r}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{body.session_id}' not found in database.",
        )

    history = get_session_history(body.session_id)
    if not _is_conversation_ready(history):
        logger.warning(f"Conversation not ready for evaluation: {body.session_id!r}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Not enough conversation turns. Send at least one message and receive one reply first.",
        )

    try:
        logger.debug(f"Running DeepEval patient evaluation for {body.session_id!r}")
        cfg = PatientEvalConfig(
            role_adherence_threshold=body.role_adherence_threshold,
            convo_quality_threshold=body.convo_quality_threshold,
        )
        result = evaluator.evaluate(
            history,
            condition=session["condition"],
            language=session["language"],
            config=cfg,
        )
        # Save evaluation result to DB
        save_evaluation(body.session_id, "patient", result)
        logger.info(f"Patient evaluation completed: {body.session_id!r}")
        
    except Exception as exc:
        logger.error(f"Patient evaluation failed: {type(exc).__name__}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Patient evaluation failed: {exc}",
        ) from exc

    return PatientEvalResponse(
        session_id=body.session_id,
        condition=result.get("condition", session["condition"]),
        language=result.get("language", session["language"]),
        metrics=result.get("metrics", []),
    )
