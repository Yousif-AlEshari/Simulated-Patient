"""src.state.session_store

Session state helpers.

This module intentionally keeps Streamlit-specific logic here so the rest of the
codebase can stay testable without Streamlit.
"""

from __future__ import annotations

from typing import Dict, List

import streamlit as st

from src.state.session_keys import (
    ACTIVE_CONDITION,
    ACTIVE_LANGUAGE,
    CONVERSATION_HISTORY,
    RUBRIC,
    RUBRIC_PATH,
    TRAINEE_GRADE,
    TRAINEE_META,
    TRAINEE_SCORED,
)


def ensure_initialized(*, default_language: str = "English") -> None:
    """Initialize expected session_state keys."""
    if CONVERSATION_HISTORY not in st.session_state:
        st.session_state[CONVERSATION_HISTORY] = []
    if ACTIVE_CONDITION not in st.session_state:
        st.session_state[ACTIVE_CONDITION] = ""
    if ACTIVE_LANGUAGE not in st.session_state:
        st.session_state[ACTIVE_LANGUAGE] = default_language

    if RUBRIC_PATH not in st.session_state:
        st.session_state[RUBRIC_PATH] = "rubrics/psychiatry_intake.json"
    if RUBRIC not in st.session_state:
        st.session_state[RUBRIC] = None

    for k in (TRAINEE_GRADE, TRAINEE_META, TRAINEE_SCORED):
        if k not in st.session_state:
            st.session_state[k] = None


def clear_all(*, default_language: str = "English") -> None:
    """Clear conversation and evaluation outputs."""
    st.session_state[CONVERSATION_HISTORY] = []
    st.session_state[ACTIVE_CONDITION] = ""
    st.session_state[ACTIVE_LANGUAGE] = default_language
    st.session_state[RUBRIC] = None
    st.session_state[TRAINEE_GRADE] = None
    st.session_state[TRAINEE_META] = None
    st.session_state[TRAINEE_SCORED] = None


def set_conversation(history: List[Dict[str, str]], *, condition: str, language: str) -> None:
    """Set a new conversation (e.g., after reset) and clear eval artifacts."""
    st.session_state[CONVERSATION_HISTORY] = history
    st.session_state[ACTIVE_CONDITION] = condition
    st.session_state[ACTIVE_LANGUAGE] = language

    st.session_state[TRAINEE_GRADE] = None
    st.session_state[TRAINEE_META] = None
    st.session_state[TRAINEE_SCORED] = None


def conversation_ready(min_turns: int = 2) -> bool:
    history = st.session_state.get(CONVERSATION_HISTORY) or []
    return len(history) >= min_turns


def get_history() -> List[Dict[str, str]]:
    return list(st.session_state.get(CONVERSATION_HISTORY) or [])


def append_message(role: str, content: str) -> None:
    history = st.session_state.get(CONVERSATION_HISTORY) or []
    history.append({"role": role, "content": content})
    st.session_state[CONVERSATION_HISTORY] = history
