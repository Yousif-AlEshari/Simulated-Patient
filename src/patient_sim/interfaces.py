"""src.patient_sim.interfaces

Interfaces for patient simulation providers.

This makes it easy to swap Groq/OpenAI/local models without touching Streamlit UI.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Protocol


Conversation = List[Dict[str, str]]


@dataclass(frozen=True)
class PatientSimConfig:
    model: str = "openai/gpt-oss-120b"
    temperature: float = 1.0
    max_completion_tokens: int = 8192
    top_p: float = 1.0
    reasoning_effort: str = "medium"
    reasoning_format: str | None = None


class PatientSimulator(Protocol):
    def generate(self, conversation: Conversation, *, config: PatientSimConfig) -> str:
        """Generate the next patient message given the full conversation."""
        ...
