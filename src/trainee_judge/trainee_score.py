"""
trainee_score.py

Deterministic scorer for trainee evaluation.

Input:
  - rubric JSON (examiner-editable)
  - judge output JSON from trainee_judge_groq.py (LLM-as-examiner)

Output:
  - fully deterministic scoring breakdown:
      - per-item points_awarded
      - total_score / total_possible / percent
      - gates applied (e.g., patient_risk_positive)
      - safety flags (e.g., SAFETY_CRITICAL) derived deterministically
      - pass/fail based on rubric.pass_criteria

Why deterministic scoring?
  - Keeps weights, gates, and pass rules under your control (rubric JSON),
    while letting the LLM provide semantic judgments + evidence.

This file DOES NOT call any LLM.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv
from src.utils.paths import default_rubric_path
from src.utils.logger import get_logger, log_call

logger = get_logger(__name__)

# Optional: reuse the same default rubric path convention as other files.
DEFAULT_RUBRIC_PATH = default_rubric_path()
load_dotenv()

# ----------------------------
# Lightweight text normalization (for gate detection)
# ----------------------------
_AR_DIACRITICS = re.compile(r"[\u064B-\u0652\u0670]")
_AR_ALEF = re.compile(r"[إأآا]")
_AR_YAA = re.compile(r"[ىي]")

# Scoring thresholds
ITEM_SCORE_PASS_THRESHOLD = 2  # Only item_score >= 2 counts as achieved (0=no, 1=partial, 2=clear)


def normalize(text: str) -> str:
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


def _patterns_for_language(obj: Dict[str, Any], language: str) -> List[str]:
    """
    Choose patterns for a language with fallback.
    """
    if language == "Arabic":
        return (obj.get("patterns_ar") or []) or (obj.get("patterns_en") or [])
    return (obj.get("patterns_en") or []) or (obj.get("patterns_ar") or [])


# ----------------------------
# Rubric loading
# ----------------------------
def load_rubric(rubric_path: str | Path = DEFAULT_RUBRIC_PATH) -> Dict[str, Any]:
    path = Path(rubric_path)
    if not path.exists():
        raise FileNotFoundError(f"Rubric not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


# ----------------------------
# Gate detection (deterministic)
# ----------------------------
_DEFAULT_PATIENT_RISK_CUES = {
    "patterns_en": [r"\b(suicid|kill myself|end my life|self[- ]harm|hurt myself)\b"],
    "patterns_ar": [r"(انتحار|اقتل نفسي|انهي حياتي|ايذاء النفس|اؤذي نفسي)"],
}


def patient_risk_positive(conversation_history: List[Dict[str, str]], rubric: Dict[str, Any], language: str) -> bool:
    """
    Detect patient suicidality/self-harm cues from patient turns (role == 'assistant').
    Uses rubric.patient_cues.risk_positive patterns when present, else defaults.
    """
    cues = (rubric or {}).get("patient_cues", {}).get("risk_positive", _DEFAULT_PATIENT_RISK_CUES)
    patterns = _patterns_for_language(cues, language)
    patient_text = " ".join(normalize(m.get("content", "")) for m in conversation_history if m.get("role") == "assistant")
    return any_match(patterns, patient_text)


def is_gate_active(gate: Optional[str], conversation_history: List[Dict[str, str]], rubric: Dict[str, Any], language: str, profile: Optional[Any] = None) -> bool:
    """
    Returns True if a rubric item gate condition is active (meaning the item should be scored).
    If profile is provided and has risk_positive, uses that instead of pattern detection.
    Unknown gates default to True (so you don't silently hide items) but log a warning.
    """
    if not gate:
        return True
    if gate == "patient_risk_positive":
        # Prefer deterministic profile flag if available
        if profile is not None and hasattr(profile, "risk_positive"):
            return bool(profile.risk_positive)
        # Fallback to pattern detection if profile not available
        return patient_risk_positive(conversation_history, rubric, language)
    # Add more gates here as you design them.
    logger.warning(f"Unknown gate '{gate}' for item — defaulting to included. Check rubric.")
    return True


# ----------------------------
# Scoring
# ----------------------------
def _index_rubric_items(rubric: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    items = rubric.get("items", [])
    if not isinstance(items, list) or not items:
        raise ValueError("Rubric must contain a non-empty 'items' list.")
    out: Dict[str, Dict[str, Any]] = {}
    for it in items:
        item_id = str(it.get("id", "")).strip()
        if not item_id:
            raise ValueError("Found rubric item with empty 'id'.")
        if item_id in out:
            raise ValueError(f"Duplicate rubric item id: '{item_id}'")
        out[item_id] = it
    return out


def _ensure_grade_has_all_items(
    grade: Any,
    rubric_item_ids: List[str],
) -> Dict[str, Any]:
    """
    If the judge output is missing item ids (e.g., schema was not enforced),
    fill them with achieved=false defaults to prevent crashes.
    Also handles the case where the LLM might have returned a non-dict output.
    """
    if not isinstance(grade, dict):
        grade = {}
    
    item_results = grade.get("item_results")
    if not isinstance(item_results, dict):
        item_results = {}
    for item_id in rubric_item_ids:
        if item_id not in item_results:
            item_results[item_id] = {
                "achieved": False,
                "confidence": 0.0,
                "evidence_turns": [],
                "rationale": "Missing from judge output; defaulted to achieved=false.",
            }
    grade["item_results"] = item_results
    grade.setdefault("flags", [])
    grade.setdefault("summary_feedback", [])
    return grade


@log_call
def score_from_judge_output(
    conversation_history: List[Dict[str, str]],
    rubric: Dict[str, Any],
    language: str,
    judge_grade: Dict[str, Any],
    *,
    attach_item_text: bool = True,
    profile: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Deterministically compute scores from judge output + rubric.

    Returns a dict ready to display in Streamlit.
    """
    logger.info(f"Scoring judge output: rubric={rubric.get('rubric_id', 'unknown')}, language={language!r}")
    
    item_index = _index_rubric_items(rubric)
    item_ids = list(item_index.keys())
    judge_grade = _ensure_grade_has_all_items(judge_grade, item_ids)
    logger.debug(f"Processing {len(item_ids)} rubric items")

    pass_cfg = rubric.get("pass_criteria") or {}
    min_percent = float(pass_cfg.get("min_percent", 0.7))
    fail_on_flags = set(pass_cfg.get("fail_on_flags", ["SAFETY_CRITICAL"]))

    # Combine judge flags with deterministic safety flags.
    flags: List[Dict[str, Any]] = list(judge_grade.get("flags") or [])

    total_possible = 0.0
    total_score = 0.0

    scored_items: List[Dict[str, Any]] = []

    for item_id in item_ids:
        it = item_index[item_id]
        weight = float(it.get("weight", 0) or 0)
        gate = it.get("gate")
        gate_active = is_gate_active(gate, conversation_history, rubric, language, profile=profile)

        jr = (judge_grade.get("item_results") or {}).get(item_id) or {}
        
        # NEW (CHANGE 2): Read item_score (0/1/2) with backward compatibility for old achieved boolean
        item_score = jr.get("item_score", None)
        if item_score is None and "achieved" in jr:
            # Backward compatibility: convert old boolean to new 3-point scale
            achieved_bool = bool(jr.get("achieved", False))
            item_score = 2 if achieved_bool else 0
        else:
            item_score = int(item_score or 0)
            if item_score not in (0, 1, 2):
                item_score = 0
        
        # Deterministic: achieved = (item_score >= ITEM_SCORE_PASS_THRESHOLD)
        # achieved determines pass/fail status, but scoring uses ordinal value (0/1/2)
        achieved = item_score >= ITEM_SCORE_PASS_THRESHOLD
        
        confidence = float(jr.get("confidence", 0.0) or 0.0)
        evidence_turns = list(jr.get("evidence_turns") or [])
        rationale = str(jr.get("rationale", "") or "")

        included = bool(gate_active)
        
        if included:
            logger.debug(f"Item {item_id}: score={item_score}, included=true, weight={weight}")
        else:
            logger.debug(f"Item {item_id}: skipped (gate inactive)")

        if included:
            total_possible += weight
            # NEW: Partial credit based on 3-point ordinal score
            # score 0 (not shown) → 0% of weight
            # score 1 (partial)    → 50% of weight
            # score 2 (clear)      → 100% of weight
            points = (item_score / 2.0) * weight
            total_score += points
        else:
            points = 0.0

        # Deterministic safety flag (regardless of what the judge returned)
        if included and bool(it.get("safety_critical", False)) and not achieved:
            logger.warning(f"Safety-critical item '{item_id}' not achieved while applicable")
            flags.append(
                {
                    "type": "SAFETY_CRITICAL",
                    "item_id": item_id,
                    "message": f"Safety-critical item '{item_id}' not achieved while applicable.",
                    "evidence_turns": evidence_turns,
                }
            )

        scored_items.append(
            {
                "id": item_id,
                "desc": it.get("desc", "") if attach_item_text else None,
                "weight": weight,
                "included": included,
                "gate": gate,
                "achieved": achieved,
                "item_score": item_score,  # NEW: Add 3-point ordinal score for transparency
                "points_awarded": points,
                "confidence": round(confidence, 3),
                "evidence_turns": evidence_turns,
                "rationale": rationale,
            }
        )

    percent = (total_score / total_possible) if total_possible > 0 else 0.0
    has_fail_flag = any(f.get("type") in fail_on_flags for f in flags)
    passed = (percent >= min_percent) and (not has_fail_flag)

    # Optional: lightweight deterministic "missing items" feedback if judge feedback is empty
    summary_feedback = list(judge_grade.get("summary_feedback") or [])
    if not summary_feedback:
        missing = [x for x in scored_items if x["included"] and not x["achieved"]]
        for x in missing[:3]:
            summary_feedback.append(f"Consider addressing: {x['id']} — {x.get('desc','')}".strip())

    return {
        "rubric_id": rubric.get("rubric_id", ""),
        "rubric_version": rubric.get("version", ""),
        "total_score": round(total_score, 3),
        "total_possible": round(total_possible, 3),
        "percent": round(percent, 3),
        "pass": bool(passed),
        "min_percent": min_percent,
        "fail_on_flags": sorted(list(fail_on_flags)),
        "flags": flags,
        "items": scored_items,
        "summary_feedback": summary_feedback,
    }


if __name__ == "__main__":
    # Quick local smoke test (no LLM needed):
    rb = load_rubric(DEFAULT_RUBRIC_PATH)
    demo_convo = [
        {"role": "user", "content": "Hello, I'm Dr. Mike. What brings you here today?"},
        {"role": "assistant", "content": "I've been feeling low for months."},
    ]
    demo_grade = {
        "rubric_id": rb.get("rubric_id"),
        "rubric_version": rb.get("version"),
        "rubric_fingerprint": "demo",
        "item_results": {it["id"]: {"achieved": False, "confidence": 0.2, "evidence_turns": [], "rationale": "demo"} for it in rb["items"]},
        "flags": [],
        "summary_feedback": [],
    }
    out = score_from_judge_output(demo_convo, rb, "English", demo_grade)
    logger.debug(f"Demo score output: {json.dumps(out, ensure_ascii=False, indent=2)}")
