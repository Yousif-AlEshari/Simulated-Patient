"""api.routes.session

Session-related helpers: timer queries and result summaries.

Endpoints provided:
  GET /api/v1/session/{session_id}/time    — remaining seconds & expired flag
  GET /api/v1/session/{session_id}/results — computed strengths/weaknesses/improvement
  POST /api/v1/session/{session_id}/end     — (optional) mark a session as expired early
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, status

from src.utils.logger import get_logger

logger = get_logger(__name__)

from api.models import SessionTimeResponse, SessionResultsResponse
from api.database import (
    get_session_info,
    is_session_active,
    time_left_seconds,
    compute_session_results,
    expire_session_now,
)

router = APIRouter(prefix="/session", tags=["Session"])


@router.get("/{session_id}/time", response_model=SessionTimeResponse)
def get_session_time(session_id: str) -> SessionTimeResponse:
    """Return how many seconds remain before the 10‑minute timer expires."""
    
    info = get_session_info(session_id)
    if info is None:
        logger.warning(f"Session not found for timer query: {session_id!r}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    
    remaining = time_left_seconds(session_id)
    if remaining < 60:
        logger.warning(f"Session nearing expiry: {session_id!r}, remaining={remaining:.1f}s")
    
    return SessionTimeResponse(
        session_id=session_id,
        remaining_seconds=remaining,
        expired=(remaining <= 0.0),
    )


@router.get("/{session_id}/profile")
def get_session_profile_endpoint(session_id: str):
    """
    Return the PatientProfile for a session as a JSON dict.
    Used by the frontend to display the examiner profile view.
    """
    import dataclasses
    from api.database import get_session_profile as _get_profile
    info = get_session_info(session_id)
    if info is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    profile = _get_profile(session_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not available for this session."
        )
    return dataclasses.asdict(profile)


@router.get("/{session_id}/results", response_model=SessionResultsResponse)
def get_session_results(session_id: str) -> SessionResultsResponse:
    """Provide a summary of strengths, weaknesses and improvement suggestions based on last trainee eval."""
    info = get_session_info(session_id)
    if info is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    results = compute_session_results(session_id)
    return SessionResultsResponse(session_id=session_id, **results)


@router.post("/{session_id}/end", response_model=SessionTimeResponse)
def end_session_early(session_id: str) -> SessionTimeResponse:
    """Force a session to expire immediately.  Useful for testing or manual termination."""
    info = get_session_info(session_id)
    if info is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    expire_session_now(session_id)
    remaining = time_left_seconds(session_id)
    return SessionTimeResponse(session_id=session_id, remaining_seconds=remaining, expired=True)
