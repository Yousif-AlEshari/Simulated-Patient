"""src.ui.app_shell

Streamlit shell: page setup + tabs.

Keep this module free of any provider-specific logic.
"""

from __future__ import annotations

from typing import Any, Optional

import streamlit as st

from src.state.session_store import ensure_initialized
from src.ui.chat_tab import render_chat_tab
from src.ui.patient_eval_tab import render_patient_eval_tab
from src.ui.trainee_eval_tab import render_trainee_eval_tab


def render_app(*, patient_simulator: Any, patient_evaluator: Any, trainee_pipeline: Any, legacy_regex_evaluator: Optional[Any] = None) -> None:
    ensure_initialized()

    st.set_page_config(page_title="Simulated Patient Chatbot", layout="wide")
    st.title("Simulated Patient Chatbot")

    tab_chat, tab_patient_eval, tab_trainee_eval = st.tabs(["Chat", "Evaluate Patient", "Evaluate Trainee"])

    with tab_chat:
        render_chat_tab(patient_simulator=patient_simulator)

    with tab_patient_eval:
        render_patient_eval_tab(patient_evaluator=patient_evaluator)

    with tab_trainee_eval:
        render_trainee_eval_tab(trainee_pipeline=trainee_pipeline, legacy_regex_evaluator=legacy_regex_evaluator)
