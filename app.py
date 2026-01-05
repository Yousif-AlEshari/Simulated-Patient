"""Streamlit entrypoint.

Run:
    streamlit run app.py

The heavy lifting lives in src/* modules so you can swap providers/evaluators.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure repo root is on sys.path (helps when running Streamlit from elsewhere).
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.utils.env import load_env

load_env()

from src.patient_sim.groq_patient_sim import GroqPatientSimulator
from src.evaluation.patient.deepeval_patient import DeepEvalPatientEvaluator
from src.evaluation.trainee.pipeline import TraineeEvalPipeline
from src.evaluation.trainee.legacy_regex import evaluate_trainee as legacy_regex_evaluate_trainee
from src.trainee_judge.trainee_judge_schema import load_rubric as load_examiner_rubric
from src.trainee_judge.trainee_judge_groq import judge_trainee_with_groq
from src.trainee_judge.trainee_score import score_from_judge_output
from src.ui.app_shell import render_app


def main() -> None:
    patient_simulator = GroqPatientSimulator()
    patient_evaluator = DeepEvalPatientEvaluator()

    trainee_pipeline = TraineeEvalPipeline(
        rubric_loader=load_examiner_rubric,
        judge_fn=judge_trainee_with_groq,
        scorer_fn=score_from_judge_output,
    )

    render_app(
        patient_simulator=patient_simulator,
        patient_evaluator=patient_evaluator,
        trainee_pipeline=trainee_pipeline,
        legacy_regex_evaluator=legacy_regex_evaluate_trainee,
    )


if __name__ == "__main__":
    main()
