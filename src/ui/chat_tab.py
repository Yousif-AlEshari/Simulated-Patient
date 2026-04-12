"""src.ui.chat_tab

Chat UI for the simulated patient.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

import streamlit as st

from src.patient_sim.interfaces import PatientSimConfig
from src.patient_sim.prompts import build_system_prompt, build_system_prompt_from_profile
from src.state.session_keys import ACTIVE_CONDITION, ACTIVE_LANGUAGE, CONVERSATION_HISTORY
from src.state.session_store import append_message, clear_all, get_history, set_conversation
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _init_history(
    condition: str,
    language: str,
    profile=None,
) -> List[Dict[str, str]]:
    if profile is not None:
        system_prompt = build_system_prompt_from_profile(profile)
    else:
        system_prompt = build_system_prompt(condition, language)
    return [{"role": "system", "content": system_prompt}]


def render_chat_tab(*, patient_simulator: Any) -> None:
    logger.debug("Rendering chat tab")
    
    condition = st.text_input("Enter the patient's condition (Ex: depression, anxiety):").strip()
    language = st.selectbox("Select the language for responses:", ["English", "Arabic"], index=0)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start / Reset conversation"):
            if not condition:
                st.warning("Please enter a condition first.")
            else:
                logger.info(f"Starting conversation: condition={condition!r}, language={language!r}")
                with st.spinner("Generating patient profile..."):
                    try:
                        profile = patient_simulator.generate_profile(condition, language)
                        st.session_state["patient_profile"] = profile
                        logger.info(f"Profile generated successfully for {condition}")
                    except Exception as e:
                        logger.warning(f"Profile generation failed: {type(e).__name__}: {e}")
                        profile = None
                        st.session_state["patient_profile"] = None
                set_conversation(
                    _init_history(condition, language, profile=st.session_state.get("patient_profile")),
                    condition=condition,
                    language=language,
                )

    with col2:
        if st.button("Clear everything"):
            logger.info("Clearing entire session")
            clear_all(default_language="English")
            st.rerun()

    chat_box = st.container(height=520)

    # Auto-init once user provides a condition.
    history = get_history()
    if condition and not history:
        logger.debug(f"Auto-initializing conversation for {condition}")
        try:
            profile = patient_simulator.generate_profile(condition, language)
            st.session_state["patient_profile"] = profile
        except Exception as e:
            logger.warning(f"Auto-init profile generation failed: {type(e).__name__}: {e}")
            profile = None
            st.session_state["patient_profile"] = None
        set_conversation(_init_history(condition, language, profile=st.session_state.get("patient_profile")), condition=condition, language=language)
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
                logger.error("GROQ_API_KEY is missing")
                st.error("GROQ_API_KEY is missing. Add it to your environment or .env file.")
            else:
                logger.debug("User message received, appending to history")
                append_message("user", user_message)
                try:
                    cfg = PatientSimConfig()
                    logger.debug(f"Generating patient response for {len(get_history())} turn conversation")
                    assistant_response = patient_simulator.generate(get_history(), config=cfg)
                    append_message("assistant", assistant_response)
                    logger.info("Patient response generated successfully")
                except Exception as e:
                    logger.error(f"LLM call failed: {type(e).__name__}: {e}", exc_info=True)
                    st.error(f"LLM call failed: {e}")

    with chat_box:
        for message in get_history():
            if message.get("role") == "user":
                st.chat_message("user").markdown(message.get("content", ""))
            elif message.get("role") == "assistant":
                st.chat_message("assistant").markdown(message.get("content", ""))

    # Examiner-only profile view
    profile = st.session_state.get("patient_profile")
    if profile is not None:
        import dataclasses
        with st.expander("Patient profile (examiner view — not visible to trainee)"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Age:** {profile.age}")
                st.write(f"**Gender:** {profile.gender}")
                st.write(f"**Occupation:** {profile.occupation}")
                st.write(f"**Severity:** {profile.symptom_severity}")
            with col2:
                st.write(f"**Response style:** {profile.response_style}")
                st.write(f"**Emotional tone:** {profile.emotional_tone}")
                st.write(f"**Risk positive:** {'YES' if profile.risk_positive else 'No'}")
            with col3:
                st.write(f"**Onset:** {profile.symptom_onset}")
                st.write(f"**Chief complaint:** {profile.chief_complaint}")
            if profile.risk_positive:
                st.warning(f"RISK: {profile.risk_detail}")
