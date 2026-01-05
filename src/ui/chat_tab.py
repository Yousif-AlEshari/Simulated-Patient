"""src.ui.chat_tab

Chat UI for the simulated patient.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

import streamlit as st

from src.patient_sim.interfaces import PatientSimConfig
from src.patient_sim.prompts import build_system_prompt
from src.state.session_keys import ACTIVE_CONDITION, ACTIVE_LANGUAGE, CONVERSATION_HISTORY
from src.state.session_store import append_message, clear_all, get_history, set_conversation


def _init_history(condition: str, language: str) -> List[Dict[str, str]]:
    return [{"role": "system", "content": build_system_prompt(condition, language)}]


def render_chat_tab(*, patient_simulator: Any) -> None:
    condition = st.text_input("Enter the patient's condition (Ex: depression, anxiety):").strip()
    language = st.selectbox("Select the language for responses:", ["English", "Arabic"], index=0)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start / Reset conversation"):
            if not condition:
                st.warning("Please enter a condition first.")
            else:
                set_conversation(_init_history(condition, language), condition=condition, language=language)

    with col2:
        if st.button("Clear everything"):
            clear_all(default_language="English")
            st.rerun()

    chat_box = st.container(height=520)

    # Auto-init once user provides a condition.
    history = get_history()
    if condition and not history:
        set_conversation(_init_history(condition, language), condition=condition, language=language)
        history = get_history()

    active_condition = st.session_state.get(ACTIVE_CONDITION, "")
    active_language = st.session_state.get(ACTIVE_LANGUAGE, "English")

    if history and condition and (condition != active_condition or language != active_language):
        st.info("Condition or language changed. Click **Start / Reset conversation** to apply the new settings.")

    user_message = st.chat_input("Type your message here...")

    if user_message:
        history = get_history()
        if not history:
            st.warning("Click Start / Reset conversation first.")
        else:
            if not os.getenv("GROQ_API_KEY"):
                st.error("GROQ_API_KEY is missing. Add it to your environment or .env file.")
            else:
                append_message("user", user_message)
                try:
                    cfg = PatientSimConfig()
                    assistant_response = patient_simulator.generate(get_history(), config=cfg)
                    append_message("assistant", assistant_response)
                except Exception as e:
                    st.error(f"LLM call failed: {e}")

    with chat_box:
        for message in get_history():
            if message.get("role") == "user":
                st.chat_message("user").markdown(message.get("content", ""))
            elif message.get("role") == "assistant":
                st.chat_message("assistant").markdown(message.get("content", ""))
