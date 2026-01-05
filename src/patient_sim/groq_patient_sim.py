"""src.patient_sim.groq_patient_sim

Groq-backed patient simulator.

This is a thin wrapper around Groq Chat Completions.
"""

from __future__ import annotations

import os
from typing import Optional

from groq import Groq

from src.patient_sim.interfaces import Conversation, PatientSimConfig


class GroqPatientSimulator:
    def __init__(self, *, api_key: Optional[str] = None) -> None:
        self._client = Groq(api_key=api_key or os.getenv("GROQ_API_KEY"))

    def generate(self, conversation: Conversation, *, config: PatientSimConfig) -> str:
        resp = self._client.chat.completions.create(
            model=config.model,
            messages=conversation,
            temperature=config.temperature,
            max_completion_tokens=config.max_completion_tokens,
            top_p=config.top_p,
            reasoning_effort=config.reasoning_effort,
            reasoning_format=config.reasoning_format,
            stream=False,
            stop=None,
        )
        return resp.choices[0].message.content
