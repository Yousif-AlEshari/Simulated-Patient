"""src.evaluation.patient.deepeval_patient

DeepEval-backed patient evaluation.

Notes:
- DeepEval uses LLM-as-a-judge for some metrics; ensure OPENAI_API_KEY is set.
- This module is optional. If DeepEval isn't installed, `available=False`.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

from src.evaluation.patient.interfaces import Conversation, PatientEvalConfig
from src.patient_sim.prompts import build_chatbot_role
from src.utils.logger import get_logger

logger = get_logger(__name__)
class DeepEvalPatientEvaluator:
    def __init__(self) -> None:
        self.available = True
        try:
            from deepeval.test_case import Turn, ConversationalTestCase  # noqa: F401
            from deepeval.metrics import RoleAdherenceMetric, ConversationalGEval  # noqa: F401
            logger.info("DeepEval initialized successfully")
        except Exception as e:
            self.available = False
            logger.warning(f"DeepEval not available: {type(e).__name__}: {e}")

    def _history_to_turns(self, conversation: Conversation):
        from deepeval.test_case import Turn

        turns = []
        for m in conversation or []:
            if m.get("role") in ("user", "assistant"):
                turns.append(Turn(role=m["role"], content=m.get("content", "")))
        return turns

    def evaluate(
        self,
        conversation: Conversation,
        *,
        condition: str,
        language: str,
        config: PatientEvalConfig,
    ) -> Dict[str, Any]:
        logger.info(f"Patient evaluation start: condition={condition!r}, language={language!r}")
        
        if not self.available:
            logger.error("DeepEval is not available; cannot evaluate patient")
            raise RuntimeError("DeepEval is not available. Install with: pip install -U deepeval")
        if not os.getenv("OPENAI_API_KEY"):
            logger.error("OPENAI_API_KEY is missing; DeepEval judges require it")
            raise RuntimeError("OPENAI_API_KEY is missing; DeepEval judges require it.")

        from deepeval.test_case import ConversationalTestCase
        from deepeval.metrics import RoleAdherenceMetric, ConversationalGEval

        turns = self._history_to_turns(conversation)
        logger.debug(f"Converted conversation to {len(turns)} turns")

        context_list = [
            f"Condition: {condition or 'N/A'}",
            f"Language: {language or 'N/A'}",
            "Rules: <=2 sentences; irrelevant/unknown -> exactly 'I don't know'; never mention being an AI.",
        ]

        test_case = ConversationalTestCase(
            turns=turns,
            scenario="Psychiatry intake interview: doctor asks questions, simulated patient answers.",
            expected_outcome=(
                "Stay in character; <=2 sentences; correct language; 'I don't know' when irrelevant/unknown; never mention AI."
            ),
            chatbot_role=build_chatbot_role(condition, language),
            context=context_list,
        )

        role_metric = RoleAdherenceMetric(threshold=config.role_adherence_threshold, include_reason=True)
        sim_metric = ConversationalGEval(
            name="PatientSimQuality",
            criteria=(
                "Evaluate the assistant as a simulated patient. Must stay in character, never mention being an AI, "
                "only discuss information relevant to the condition, respond in the selected language, keep each answer "
                "to max 2 sentences, and if irrelevant/unknown reply exactly: I don't know."
            ),
            threshold=config.convo_quality_threshold,
        )

        results = []
        for metric in (role_metric, sim_metric):
            logger.debug(f"Running metric: {metric.__class__.__name__}")
            metric.measure(test_case)
            score = getattr(metric, "score", None)
            logger.info(f"Metric {metric.__class__.__name__}: score={score}")
            results.append(
                {
                    "name": getattr(metric, "name", metric.__class__.__name__),
                    "class": metric.__class__.__name__,
                    "score": score,
                    "threshold": getattr(metric, "threshold", None),
                    "passed": metric.is_successful(),
                    "reason": getattr(metric, "reason", ""),
                }
            )

        logger.info(f"Patient evaluation finished: {len(results)} metrics evaluated")
        return {
            "condition": condition,
            "language": language,
            "metrics": results,
        }
