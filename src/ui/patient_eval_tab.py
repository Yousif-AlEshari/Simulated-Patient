"""src.ui.patient_eval_tab

Patient evaluation UI.

Default implementation uses DeepEval, but the UI calls an abstract evaluator.
"""

from __future__ import annotations

import os
from typing import Any

import streamlit as st

from src.evaluation.patient.interfaces import PatientEvalConfig
from src.state.session_keys import ACTIVE_CONDITION, ACTIVE_LANGUAGE
from src.state.session_store import conversation_ready, get_history


def render_patient_eval_tab(*, patient_evaluator: Any) -> None:
    st.subheader("Patient evaluation")

    if not getattr(patient_evaluator, "available", True):
        st.warning("DeepEval not installed. Install with: `pip install -U deepeval`")
        return

    if not os.getenv("OPENAI_API_KEY"):
        st.warning("OPENAI_API_KEY is missing. Add it to your environment or .env file to enable DeepEval judges.")
        return

    if not conversation_ready():
        st.info("Not enough turns yet. Have at least one trainee message and one patient reply.")
        return

    role_threshold = st.slider("Role adherence threshold", 0.0, 1.0, 0.8, 0.05)
    geval_threshold = st.slider("Conversation quality threshold", 0.0, 1.0, 0.7, 0.05)

    if st.button("Run patient evaluation"):
        try:
            cfg = PatientEvalConfig(role_adherence_threshold=role_threshold, convo_quality_threshold=geval_threshold)
            out = patient_evaluator.evaluate(
                get_history(),
                condition=st.session_state.get(ACTIVE_CONDITION, ""),
                language=st.session_state.get(ACTIVE_LANGUAGE, "English"),
                config=cfg,
            )

            for m in out.get("metrics", []):
                with st.expander(f"{m.get('class')} results", expanded=True):
                    st.write("Score:", m.get("score"))
                    st.write("Threshold:", m.get("threshold"))
                    st.write("Passed:", m.get("passed"))
                    st.write("Reason:", m.get("reason", ""))
        except Exception as e:
            st.error(f"Patient evaluation failed: {e}")
