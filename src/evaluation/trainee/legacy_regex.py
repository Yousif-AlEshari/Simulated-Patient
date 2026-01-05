"""src.evaluation.trainee.legacy_regex

Legacy (regex/pattern-based) trainee evaluator.

Kept for comparison/baseline. It is deterministic and does NOT call any LLM.

This file is adapted from your original `evaluation_engine.py`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.paths import resolve_rubric_path


# ----------------------------
# Simple text normalization
# ----------------------------
_AR_DIACRITICS = re.compile(r"[\u064B-\u0652\u0670]")
_AR_ALEF = re.compile(r"[إأآا]")
_AR_YAA = re.compile(r"[ىي]")


def normalize(text: str) -> str:
    """Normalize English/Arabic text for robust matching."""
    t = (text or "").strip().lower()
    t = _AR_DIACRITICS.sub("", t)
    t = _AR_ALEF.sub("ا", t)
    t = _AR_YAA.sub("ي", t)
    t = re.sub(r"\s+", " ", t)
    return t


def any_match(patterns: List[str], text: str) -> bool:
    for p in patterns or []:
        if re.search(p, text, flags=re.IGNORECASE):
            return True
    return False


def find_evidence(patterns: List[str], messages: List[str]) -> Optional[str]:
    for m in messages or []:
        nm = normalize(m)
        if any_match(patterns, nm):
            return m
    return None


# ----------------------------
# Rubric loading (JSON)
# ----------------------------

def load_rubric(rubric_path: str | Path) -> Dict[str, Any]:
    path = Path(rubric_path)
    if not path.exists():
        raise FileNotFoundError(f"Rubric JSON not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        rubric = json.load(f)
    _validate_rubric_minimal(rubric)
    return rubric


def _validate_rubric_minimal(rubric: Dict[str, Any]) -> None:
    if not isinstance(rubric, dict):
        raise ValueError("Rubric must be a JSON object (dict).")

    items = rubric.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("Rubric must include a non-empty 'items' list.")

    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"Rubric item #{i} must be an object.")
        for k in ("id", "desc", "weight"):
            if k not in item:
                raise ValueError(f"Rubric item #{i} missing required field: '{k}'")
        if not isinstance(item["weight"], (int, float)) or item["weight"] < 0:
            raise ValueError(f"Rubric item '{item.get('id')}' has invalid 'weight' (must be >= 0).")

        pe = item.get("patterns_en", [])
        pa = item.get("patterns_ar", [])
        if not isinstance(pe, list) or not isinstance(pa, list):
            raise ValueError(f"Rubric item '{item.get('id')}' patterns must be lists.")
        if len(pe) == 0 and len(pa) == 0:
            raise ValueError(f"Rubric item '{item.get('id')}' must include patterns_en and/or patterns_ar.")


def _patterns_for_language(obj: Dict[str, Any], language: str) -> List[str]:
    if language == "Arabic":
        return (obj.get("patterns_ar") or []) or (obj.get("patterns_en") or [])
    return (obj.get("patterns_en") or []) or (obj.get("patterns_ar") or [])


# ----------------------------
# Patient cue detection (risk)
# ----------------------------
_DEFAULT_PATIENT_RISK_CUES = {
    "patterns_en": [r"\b(suicid|kill myself|end my life|self[- ]harm|hurt myself)\b"],
    "patterns_ar": [r"(انتحار|اقتل نفسي|انهي حياتي|ايذاء النفس|اؤذي نفسي)"],
}


def patient_risk_positive(patient_msgs: List[str], rubric: Dict[str, Any], language: str) -> bool:
    cue = (rubric or {}).get("patient_cues", {}).get("risk_positive", _DEFAULT_PATIENT_RISK_CUES)
    patterns = _patterns_for_language(cue, language)
    joined = " ".join(normalize(m) for m in (patient_msgs or []))
    return any_match(patterns, joined)


# ----------------------------
# Main evaluator
# ----------------------------

def evaluate_trainee(
    conversation_history: List[Dict[str, str]],
    condition: str,
    language: str,
    rubric: Optional[Dict[str, Any]] = None,
    rubric_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Evaluate trainee messages using the rubric patterns (no LLM judge)."""

    if rubric is None:
        p = resolve_rubric_path(rubric_path)
        rubric = load_rubric(p)

    trainee_msgs = [m.get("content", "") for m in conversation_history if m.get("role") == "user"]
    patient_msgs = [m.get("content", "") for m in conversation_history if m.get("role") == "assistant"]

    risk_positive = patient_risk_positive(patient_msgs, rubric, language)

    checklist_results = []
    total = 0.0
    total_possible = 0.0
    flags = []

    for item in rubric["items"]:
        weight = float(item.get("weight", 0))
        total_possible += weight

        if item.get("gate") == "patient_risk_positive" and not risk_positive:
            total_possible -= weight
            continue

        patterns = _patterns_for_language(item, language)
        ev = find_evidence(patterns, trainee_msgs)
        score = weight if ev else 0.0

        checklist_results.append(
            {
                "id": item.get("id"),
                "desc": item.get("desc"),
                "score": score,
                "weight": weight,
                "evidence": ev,
            }
        )
        total += score

        if item.get("safety_critical") and risk_positive and not ev:
            flags.append(
                {
                    "type": "SAFETY_CRITICAL",
                    "id": item.get("id"),
                    "message": "Patient risk cue present, but trainee did not assess plan/intent/means/access.",
                }
            )

    globals_cfg = rubric.get("globals") or {}
    comm_max = int(globals_cfg.get("communication_max", 5))
    judg_max = int(globals_cfg.get("judgment_max", 5))

    empathy = next((x for x in checklist_results if x["id"] == "empathy_validation"), None)
    summary = next((x for x in checklist_results if x["id"] == "summary_next_steps"), None)

    comm_raw = (1 if empathy and empathy["score"] > 0 else 0) + (1 if summary and summary["score"] > 0 else 0)
    communication = min(comm_max, max(1, round(2 + comm_raw * 1.5)))

    pct = (total / total_possible) if total_possible > 0 else 0.0
    judgment = 1 + (judg_max - 1) * pct
    if any(f["type"] == "SAFETY_CRITICAL" for f in flags):
        judgment = min(judgment, 2)
    judgment = min(judg_max, max(1, round(judgment)))

    pass_cfg = rubric.get("pass_criteria") or {}
    min_percent = float(pass_cfg.get("min_percent", 0.7))
    fail_on_flags = set(pass_cfg.get("fail_on_flags", ["SAFETY_CRITICAL"]))

    has_fail_flag = any(f.get("type") in fail_on_flags for f in flags)
    passed = (pct >= min_percent) and not has_fail_flag

    feedback = []
    if empathy and empathy["score"] == 0:
        feedback.append("Add a brief validation/empathy statement when the patient shares distress.")
    if risk_positive and not any(x["id"] == "risk_depth" and x["score"] > 0 for x in checklist_results):
        feedback.append(
            "When suicidality/self-harm is mentioned, assess plan/intent/means/access and escalate safety planning."
        )
    if summary and summary["score"] == 0:
        feedback.append("End with a short summary and clear next steps.")

    return {
        "condition": condition,
        "language": language,
        "rubric_id": rubric.get("rubric_id"),
        "rubric_version": rubric.get("version"),
        "checklist": checklist_results,
        "globals": {"communication": communication, "judgment": judgment},
        "flags": flags,
        "total_score": total,
        "total_possible": total_possible,
        "percent": round(pct, 3),
        "pass": passed,
        "feedback": feedback,
    }
