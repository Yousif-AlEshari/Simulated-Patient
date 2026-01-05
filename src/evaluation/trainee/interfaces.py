"""src.evaluation.trainee.interfaces

Interfaces and simple types for trainee evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, Tuple


Conversation = List[Dict[str, str]]


@dataclass(frozen=True)
class TraineeEvalResult:
    scored: Dict[str, Any]
    judge_grade: Optional[Dict[str, Any]] = None
    judge_meta: Optional[Dict[str, Any]] = None


class TraineeJudge(Protocol):
    def judge(
        self,
        conversation: Conversation,
        *,
        language: str,
        condition: str,
        rubric: Dict[str, Any],
        config: Any,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Return (grade_json, meta)."""
        ...


class TraineeScorer(Protocol):
    def score(
        self,
        conversation: Conversation,
        *,
        language: str,
        rubric: Dict[str, Any],
        judge_grade: Dict[str, Any],
    ) -> Dict[str, Any]:
        ...
