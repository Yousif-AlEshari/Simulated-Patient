"""api.routes.chat

Chat endpoints:
  POST   /api/v1/chat/start               — create a new session
  POST   /api/v1/chat/message             — send a trainee message, get patient reply
  DELETE /api/v1/chat/session/{session_id} — delete a session
"""

from __future__ import annotations

import os
import json as _json
from typing import Annotated
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from src.utils.logger import get_logger

logger = get_logger(__name__)

from api.dependencies import get_patient_simulator
from api.models import (
    ChatMessageRequest,
    ChatMessageResponse,
    DeleteSessionResponse,
    StartSessionRequest,
    StartSessionResponse,
)
from api.database import (
    save_session,
    add_message,
    get_session_history,
    get_session_info,
    delete_session_data,
    is_session_active,
    time_left_seconds,
    get_session_profile,
)
from src.patient_sim.groq_patient_sim import GroqPatientSimulator
from src.patient_sim.interfaces import PatientSimConfig
from src.patient_sim.prompts import build_system_prompt, build_system_prompt_from_profile

router = APIRouter(prefix="/chat", tags=["Chat"])


def _require_session(session_id: str):
    """Resolve a session or raise 404."""
    session = get_session_info(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found in database.",
        )
    return session


@router.post("/start", response_model=StartSessionResponse, status_code=status.HTTP_201_CREATED)
def start_session(
    body: StartSessionRequest,
    simulator: Annotated[GroqPatientSimulator, Depends(get_patient_simulator)],
) -> StartSessionResponse:
    """
    Create a new simulation session.

    Returns a `session_id` that must be passed to all subsequent endpoints.
    """
    logger.info(f"Starting new session: condition={body.condition!r}, language={body.language!r}")
    
    if not body.condition.strip():
        logger.warning("Invalid condition (empty string)")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="condition must not be empty.",
        )

    import uuid
    session_id = str(uuid.uuid4())
    language = body.language if body.language in ("English", "Arabic") else "English"
    
    logger.debug(f"Generated session_id={session_id}")
    
    # Generate a random patient profile for this session
    try:
        profile = simulator.generate_profile(body.condition.strip(), language)
        # Serialize profile to JSON for storage, excluding condition/language
        # (those are already stored as separate columns)
        import dataclasses
        profile_dict = dataclasses.asdict(profile)
        profile_dict.pop("condition", None)
        profile_dict.pop("language", None)
        profile_json = _json.dumps(profile_dict)
        system_prompt_text = build_system_prompt_from_profile(profile)
        logger.info(f"Patient profile generated successfully for {session_id}")
    except Exception as e:
        # Fallback: use the old static system prompt if profile generation fails
        logger.warning(f"Profile generation failed, using fallback: {type(e).__name__}: {e}")
        profile_json = None
        system_prompt_text = build_system_prompt(body.condition.strip(), language)
    
    # Save session and initial system prompt
    save_session(session_id, body.condition.strip(), language, profile_json=profile_json)
    add_message(session_id, "system", system_prompt_text)
    logger.info(f"Session started: {session_id}")

    # fetch the record to obtain expires_at value
    info = get_session_info(session_id) or {}
    exp = info.get("expires_at")
    if isinstance(exp, datetime):
        exp = exp.isoformat()

    return StartSessionResponse(
        session_id=session_id,
        condition=body.condition.strip(),
        language=language,
        expires_at=exp,
    )


@router.post("/message", response_model=ChatMessageResponse)
def send_message(
    body: ChatMessageRequest,
    simulator: Annotated[GroqPatientSimulator, Depends(get_patient_simulator)],
) -> ChatMessageResponse:
    """
    Send a trainee message to the simulated patient and receive the patient's reply.
    """
    if not os.getenv("GROQ_API_KEY"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GROQ_API_KEY is not configured on the server.",
        )

    _require_session(body.session_id)

    # enforce the 10‑minute timer
    if not is_session_active(body.session_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Session has expired; chat is no longer active.",
        )

    if not body.message.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="message must not be empty.",
        )

    # Save user message
    add_message(body.session_id, "user", body.message)

    try:
        cfg_kwargs = {}
        if body.model:
            cfg_kwargs["model"] = body.model
        if body.reasoning_effort:
            cfg_kwargs["reasoning_effort"] = body.reasoning_effort

        cfg = PatientSimConfig(**cfg_kwargs)
        history = get_session_history(body.session_id)
        reply = simulator.generate(history, config=cfg)
        
        # Save assistant message
        add_message(body.session_id, "assistant", reply)
        
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM call failed: {exc}",
        ) from exc

    return ChatMessageResponse(session_id=body.session_id, role="assistant", content=reply)


@router.delete("/session/{session_id}", response_model=DeleteSessionResponse)
def delete_session(session_id: str) -> DeleteSessionResponse:
    """Delete a session and its conversation history."""
    deleted = False
    if get_session_info(session_id):
        delete_session_data(session_id)
        deleted = True
    return DeleteSessionResponse(session_id=session_id, deleted=deleted)
