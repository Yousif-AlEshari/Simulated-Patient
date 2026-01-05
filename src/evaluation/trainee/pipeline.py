"""src.evaluation.trainee.pipeline

High-level orchestrator for trainee evaluation.

This is the single "integration point" the UI should call.
Swap judge/scorer implementations here to enable drop-in changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from src.evaluation.trainee.interfaces import Conversation, TraineeEvalResult
from src.utils.paths import resolve_rubric_path


@dataclass(frozen=True)
class TraineeEvalPipeline:
    """Orchestrates: load rubric -> judge -> deterministic score."""

    rubric_loader: Any
    judge_fn: Any
    scorer_fn: Any

    def load_rubric(self, rubric_path: Optional[str]) -> Dict[str, Any]:
        p = resolve_rubric_path(rubric_path)
        return self.rubric_loader(p)

    def run(
        self,
        conversation: Conversation,
        *,
        language: str,
        condition: str,
        rubric: Optional[Dict[str, Any]] = None,
        rubric_path: Optional[str] = None,
        judge_config: Optional[Any] = None,
    ) -> TraineeEvalResult:
        rb = rubric or self.load_rubric(rubric_path)

        judge_kwargs = {
            "language": language,
            "condition": condition,
            "rubric": rb,
        }
        if judge_config is not None:
            judge_kwargs["config"] = judge_config

        grade, meta = self.judge_fn(conversation, **judge_kwargs)

        scored = self.scorer_fn(
            conversation,
            rubric=rb,
            language=language,
            judge_grade=grade,
        )
        return TraineeEvalResult(scored=scored, judge_grade=grade, judge_meta=meta)
