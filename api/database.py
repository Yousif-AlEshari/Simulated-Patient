"""api.database

MongoDB database handler.
Uses pymongo for all persistence. Connection URI is read from the
MONGODB_URI environment variable (falls back to localhost).

Collections:
    sessions     — one doc per simulation session
    messages     — conversation history
    evaluations  — patient / trainee evaluation results
"""

import json
import os
from datetime import datetime, timedelta, timezone

from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection

from src.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

_MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
_DB_NAME = "simulated_patient"

_client: MongoClient | None = None

_SESSION_TIME = 15


def _get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(_MONGODB_URI)
    return _client


def _db():
    return _get_client()[_DB_NAME]


def _sessions() -> Collection:
    return _db()["sessions"]


def _messages() -> Collection:
    return _db()["messages"]


def _evaluations() -> Collection:
    return _db()["evaluations"]


# ---------------------------------------------------------------------------
# Init (creates indexes)
# ---------------------------------------------------------------------------

def init_db():
    """Create indexes so lookups by session_id are fast."""
    logger.info("Initializing MongoDB database")
    _sessions().create_index([("session_id", ASCENDING)], unique=True, background=True)
    _messages().create_index([("session_id", ASCENDING)], background=True)
    _messages().create_index([("created_at", ASCENDING)], background=True)
    _evaluations().create_index([("session_id", ASCENDING)], background=True)
    _evaluations().create_index([("created_at", ASCENDING)], background=True)
    logger.debug("Database indexes created successfully")


# ---------------------------------------------------------------------------
# Session CRUD
# ---------------------------------------------------------------------------

def save_session(session_id: str, condition: str, language: str, profile_json: str = None):
    """Insert a new session document with a timed minute expiry."""
    logger.info(f"Saving session: session_id={session_id!r}, condition={condition!r}, language={language!r}")
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=_SESSION_TIME)
    doc = {
        "session_id": session_id,
        "condition": condition,
        "language": language,
        "created_at": now,
        "expires_at": expires_at,
        "profile": profile_json,  # raw JSON string or None
    }
    _sessions().insert_one(doc)
    logger.debug(f"Session saved, expires at {expires_at.isoformat()}")


def get_session_info(session_id: str) -> dict | None:
    """Return the session document as a plain dict, or None."""
    logger.debug(f"Fetching session info: {session_id!r}")
    doc = _sessions().find_one({"session_id": session_id}, {"_id": 0})
    if doc:
        logger.debug(f"Session found: expires_at check for {session_id!r}")
    else:
        logger.warning(f"Session not found: {session_id!r}")
    return doc  # already a dict; expires_at is a datetime object


def get_session_profile(session_id: str):
    """Return a PatientProfile dataclass for a session, or None."""
    from src.patient_sim.interfaces import PatientProfile

    doc = _sessions().find_one(
        {"session_id": session_id},
        {"condition": 1, "language": 1, "profile": 1, "_id": 0},
    )
    if not doc or not doc.get("profile"):
        return None
    try:
        data = json.loads(doc["profile"])
        data.pop("condition", None)
        data.pop("language", None)
        return PatientProfile(
            condition=doc["condition"],
            language=doc["language"],
            **data,
        )
    except Exception:
        return None


def delete_session_data(session_id: str):
    """Remove a session and all its related messages and evaluations."""
    _messages().delete_many({"session_id": session_id})
    _evaluations().delete_many({"session_id": session_id})
    _sessions().delete_one({"session_id": session_id})


# ---------------------------------------------------------------------------
# Message CRUD
# ---------------------------------------------------------------------------

def add_message(session_id: str, role: str, content: str):
    """Append a message to the conversation history."""
    _messages().insert_one(
        {
            "session_id": session_id,
            "role": role,
            "content": content,
            "created_at": datetime.now(timezone.utc),
        }
    )


def get_session_history(session_id: str) -> list[dict]:
    """Return all messages for a session, ordered by creation time."""
    cursor = _messages().find(
        {"session_id": session_id},
        {"_id": 0, "role": 1, "content": 1},
        sort=[("created_at", ASCENDING)],
    )
    return [{"role": m["role"], "content": m["content"]} for m in cursor]


# ---------------------------------------------------------------------------
# Evaluation CRUD
# ---------------------------------------------------------------------------

def save_evaluation(session_id: str, eval_type: str, score_data: dict):
    """Persist an evaluation result."""
    _evaluations().insert_one(
        {
            "session_id": session_id,
            "eval_type": eval_type,
            "score_data": score_data,  # store as a real dict, not JSON string
            "created_at": datetime.now(timezone.utc),
        }
    )


def get_latest_trainee_eval(session_id: str) -> dict | None:
    """Return the most recent trainee evaluation score_data dict, or None."""
    doc = _evaluations().find_one(
        {"session_id": session_id, "eval_type": "trainee"},
        {"_id": 0, "score_data": 1},
        sort=[("created_at", -1)],
    )
    if not doc:
        return None
    return doc["score_data"]


# ---------------------------------------------------------------------------
# Timer helpers
# ---------------------------------------------------------------------------

def is_session_active(session_id: str) -> bool:
    """Return True if the session exists and has not expired yet."""
    doc = _sessions().find_one(
        {"session_id": session_id},
        {"expires_at": 1, "_id": 0},
    )
    if doc is None:
        return False
    expires = doc.get("expires_at")
    if not expires:
        return True
    # ensure both sides are tz-aware
    now = datetime.now(timezone.utc)
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    return now < expires


def time_left_seconds(session_id: str) -> float:
    """Return number of seconds remaining for a session, or 0.0."""
    doc = _sessions().find_one(
        {"session_id": session_id},
        {"expires_at": 1, "_id": 0},
    )
    if not doc or not doc.get("expires_at"):
        return 0.0
    expires = doc["expires_at"]
    now = datetime.now(timezone.utc)
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    delta = expires - now
    return max(0.0, delta.total_seconds())


def expire_session_now(session_id: str):
    """Force a session to expire immediately."""
    _sessions().update_one(
        {"session_id": session_id},
        {"$set": {"expires_at": datetime.now(timezone.utc)}},
    )


# ---------------------------------------------------------------------------
# Results helpers
# ---------------------------------------------------------------------------

def compute_session_results(session_id: str) -> dict:
    """Generate strengths/weaknesses/improvement from the latest trainee eval."""
    eval_data = get_latest_trainee_eval(session_id)
    strengths: list[str] = []
    weaknesses: list[str] = []
    if eval_data and isinstance(eval_data, dict):
        for item in eval_data.get("items", []):
            desc = item.get("desc") or item.get("id")
            if item.get("achieved"):
                strengths.append(desc)
            else:
                weaknesses.append(desc)
    improvement = "Review the items you missed and seek feedback from an examiner."
    return {"strengths": strengths, "weaknesses": weaknesses, "improvement": improvement}
