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
from src.utils.logger import get_logger, log_call

logger = get_logger(__name__)


@dataclass(frozen=True)
class TraineeEvalPipeline:
    """Orchestrates: load rubric -> judge -> deterministic score."""

    rubric_loader: Any
    judge_fn: Any
    scorer_fn: Any

    def load_rubric(self, rubric_path: Optional[str]) -> Dict[str, Any]:
        p = resolve_rubric_path(rubric_path)
        logger.debug(f"Loading rubric from {p}")
        return self.rubric_loader(p)

    @log_call
    def run(
        self,
        conversation: Conversation,
        *,
        language: str,
        condition: str,
        rubric: Optional[Dict[str, Any]] = None,
        rubric_path: Optional[str] = None,
        judge_config: Optional[Any] = None,
        profile: Optional[Any] = None,
    ) -> TraineeEvalResult:
        logger.info(f"Pipeline run start: condition={condition!r}, language={language!r}")
        
        rb = rubric or self.load_rubric(rubric_path)
        logger.debug(f"Rubric loaded: {rb.get('rubric_id', 'unknown')}")

        judge_kwargs = {
            "language": language,
            "condition": condition,
            "rubric": rb,
        }
        if judge_config is not None:
            judge_kwargs["config"] = judge_config

        try:
            grade, meta = self.judge_fn(conversation, **judge_kwargs)
            logger.info(f"Judge returned: grade={grade}")
        except Exception as e:
            logger.error(f"Judge function failed: {type(e).__name__}: {e}", exc_info=True)
            raise

        try:
            scored = self.scorer_fn(
                conversation,
                rubric=rb,
                language=language,
                judge_grade=grade,
                profile=profile,
            )
            logger.info("Scoring completed")
        except Exception as e:
            logger.error(f"Scorer function failed: {type(e).__name__}: {e}", exc_info=True)
            raise
        
        return TraineeEvalResult(scored=scored, judge_grade=grade, judge_meta=meta)
