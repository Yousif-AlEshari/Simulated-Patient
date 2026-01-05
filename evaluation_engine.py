"""Compatibility wrapper.

If you previously imported `evaluation_engine.evaluate_trainee`, keep working after
moving the actual implementation into `src.evaluation.trainee.legacy_regex`.
"""

from src.evaluation.trainee.legacy_regex import evaluate_trainee  # noqa: F401
