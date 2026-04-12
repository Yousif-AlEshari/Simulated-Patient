"""api.routes.trainee_eval

Trainee evaluation endpoints:
  POST /api/v1/eval/trainee — run LLM judge + deterministic scorer
  GET  /api/v1/rubric        — return the default (or specified) rubric metadata
"""

from __future__ import annotations

import os
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.utils.logger import get_logger

logger = get_logger(__name__)

from api.dependencies import get_trainee_pipeline
from api.models import RubricResponse, TraineeEvalRequest, TraineeEvalResponse
from api.database import get_session_info, get_session_history, save_evaluation, get_session_profile
from src.evaluation.trainee.pipeline import TraineeEvalPipeline
from src.trainee_judge.trainee_judge_groq import GroqJudgeConfig

router = APIRouter(tags=["Evaluation"])


def _is_conversation_ready(history: list, min_turns: int = 2) -> bool:
    non_system = [m for m in history if m.get("role") != "system"]
    return len(non_system) >= min_turns


@router.post("/eval/trainee", response_model=TraineeEvalResponse)
def evaluate_trainee(
    body: TraineeEvalRequest,
    pipeline: Annotated[TraineeEvalPipeline, Depends(get_trainee_pipeline)],
) -> TraineeEvalResponse:
    """
    Evaluate the trainee's performance using the LLM judge and deterministic scorer.

    Requires at least one trainee message and one patient reply in the session.
    Requires `GROQ_API_KEY` to be configured.
    """
    logger.info(f"Trainee evaluation triggered: session_id={body.session_id!r}")
    
    if not os.getenv("GROQ_API_KEY"):
        logger.error("GROQ_API_KEY not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GROQ_API_KEY is not configured on the server.",
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

    # Build judge config from request overrides.
    judge_config = GroqJudgeConfig(
        model=body.model or "openai/gpt-oss-120b",
        temperature=0.0,
        seed=body.seed,
        reasoning_effort=body.reasoning_effort or "medium",
        max_completion_tokens=body.max_completion_tokens,
        strict_schema=body.strict_schema,
    )
    logger.debug(f"Judge config: model={judge_config.model}, temp={judge_config.temperature}")

    # Get patient profile for risk gate detection
    profile = get_session_profile(body.session_id)

    try:
        logger.debug(f"Running trainee evaluation pipeline for {body.session_id!r}")
        result = pipeline.run(
            history,
            language=session["language"],
            condition=session["condition"],
            rubric_path=body.rubric_path or None,
            judge_config=judge_config,
            profile=profile,
        )
        # Save evaluation result to DB
        save_evaluation(body.session_id, "trainee", result.scored)
        logger.info(f"Trainee evaluation completed: {body.session_id!r}")
        
    except Exception as exc:
        logger.error(f"Trainee evaluation failed: {type(exc).__name__}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Trainee evaluation failed: {exc}",
        ) from exc

    scored = result.scored
    return TraineeEvalResponse(
        session_id=body.session_id,
        rubric_id=scored.get("rubric_id", ""),
        rubric_version=scored.get("rubric_version", ""),
        total_score=scored.get("total_score", 0.0),
        total_possible=scored.get("total_possible", 0.0),
        percent=scored.get("percent", 0.0),
        passed=scored.get("pass", False),
        min_percent=scored.get("min_percent", 0.7),
        flags=scored.get("flags", []),
        items=scored.get("items", []),
        summary_feedback=scored.get("summary_feedback", []),
        judge_meta=result.judge_meta,
    )


@router.get("/rubric", response_model=RubricResponse)
def get_rubric(
    path: Optional[str] = Query(None, description="Path to rubric JSON. Omit to use the default rubric."),
    pipeline: Annotated[TraineeEvalPipeline, Depends(get_trainee_pipeline)] = None,
) -> RubricResponse:
    """
    Return rubric metadata (id, version, item count, pass criteria, items list).
    """
    try:
        rb = pipeline.load_rubric(path)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to load rubric: {exc}",
        ) from exc

    return RubricResponse(
        rubric_id=rb.get("rubric_id", ""),
        version=rb.get("version", ""),
        item_count=len(rb.get("items", [])),
        pass_criteria=rb.get("pass_criteria", {}),
        items=rb.get("items", []),
    )
