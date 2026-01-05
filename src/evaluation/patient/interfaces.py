"""src.evaluation.patient.interfaces

Interfaces for patient evaluation implementations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Protocol


Conversation = List[Dict[str, str]]


@dataclass(frozen=True)
class PatientEvalConfig:
    role_adherence_threshold: float = 0.8
    convo_quality_threshold: float = 0.7


class PatientEvaluator(Protocol):
    available: bool

    def evaluate(
        self,
        conversation: Conversation,
        *,
        condition: str,
        language: str,
        config: PatientEvalConfig,
    ) -> Dict[str, Any]:
        """Return a JSON-serializable result."""
        ...
