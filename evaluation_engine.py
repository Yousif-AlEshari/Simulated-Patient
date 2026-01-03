# import re
# from dataclasses import dataclass
# from typing import List, Dict, Any, Tuple, Optional

# # ----------------------------
# # Simple text normalization
# # ----------------------------
# _AR_DIACRITICS = re.compile(r"[\u064B-\u0652\u0670]")
# _AR_ALEF = re.compile(r"[إأآا]")
# _AR_YAA = re.compile(r"[ىي]")

# def normalize(text: str) -> str:
#     t = text.strip().lower()
#     # Arabic light normalization (safe for MVP)
#     t = _AR_DIACRITICS.sub("", t)
#     t = _AR_ALEF.sub("ا", t)
#     t = _AR_YAA.sub("ي", t)
#     t = re.sub(r"\s+", " ", t)
#     return t

# # any_match checks if any regex pattern appears in a normalized string.
# def any_match(patterns: List[str], text: str) -> bool:
#     for p in patterns:
#         if re.search(p, text, flags=re.IGNORECASE):
#             return True
#     return False
# # find_evidence loops through trainee messages, returns the first message that matches.
# def find_evidence(patterns: List[str], messages: List[str]) -> Optional[str]:
#     for m in messages:
#         nm = normalize(m)
#         if any_match(patterns, nm):
#             return m
#     return None

# # ----------------------------
# # Rubric (MVP: generic intake)
# # ----------------------------
# RUBRIC = {
#     "items": [
#         {
#             "id": "intro_agenda",
#             "desc": "Sets role/agenda (intro + purpose).",
#             "weight": 2,
#             "patterns_en": [r"\b(i am|i'm)\b.*\b(doctor|psychiatrist|clinician)\b", r"\b(today|i'd like to|i want to)\b.*\b(ask|talk|understand)\b"],
#             "patterns_ar": [r"انا.*(طبيب|طبيبه|طبيب نفسي)", r"(اليوم|حاب|اريد).*(اسال|نتحدث|افهم)"],
#         },
#         {
#             "id": "open_ended",
#             "desc": "Starts with an open question.",
#             "weight": 2,
#             "patterns_en": [r"\b(tell me about|what brings you|what's been going on)\b"],
#             "patterns_ar": [r"(احكي لي|ايش جابك|شو صاير معك|ماذا يحدث)"],
#         },
#         {
#             "id": "timeline_impairment",
#             "desc": "Asks duration/timeline and functional impact.",
#             "weight": 3,
#             "patterns_en": [r"\b(how long|since when|when did this start)\b", r"\b(affect|impact)\b.*\b(work|school|sleep|daily)\b"],
#             "patterns_ar": [r"(من متى|صار لك).*", r"(اثر|ياثر).*(شغل|دراسه|نوم|حياتك)"],
#         },
#         {
#             "id": "past_tx",
#             "desc": "Past psych history + treatment/meds/therapy.",
#             "weight": 2,
#             "patterns_en": [r"\b(before|previously)\b.*\b(depression|anxiety|therapy|medication|antidepressant)\b", r"\b(are you on|have you taken)\b.*\b(meds|medication)\b"],
#             "patterns_ar": [r"(سابقا|قبل).*(علاج|ادويه|دواء|جلسات)", r"(هل تاخذ|هل اخذت).*(دواء|ادويه)"],
#         },
#         {
#             "id": "substance",
#             "desc": "Asks about alcohol/drugs/substance use.",
#             "weight": 2,
#             "patterns_en": [r"\b(alcohol|drugs|substance|weed|cannabis)\b"],
#             "patterns_ar": [r"(كحول|مخدرات|حشيش|مواد)"],
#         },
#         {
#             "id": "empathy_validation",
#             "desc": "Empathy/validation statement.",
#             "weight": 2,
#             "patterns_en": [r"\b(that sounds|i'm sorry|thank you for sharing|that must be)\b"],
#             "patterns_ar": [r"(هذا صعب|اسف|شكرا لمشاركتك|لازم يكون صعب)"],
#         },
#         {
#             "id": "risk_screen",
#             "desc": "Screens for self-harm/suicidal ideation.",
#             "weight": 4,
#             "patterns_en": [r"\b(suicid|self[- ]harm|hurt yourself|end your life|kill yourself)\b"],
#             "patterns_ar": [r"(انتحار|ايذاء النفس|تؤذي نفسك|تنهي حياتك)"],
#         },
#         {
#             "id": "risk_depth",
#             "desc": "If risk present, asks plan/intent/means/access.",
#             "weight": 5,
#             "patterns_en": [r"\b(plan|intent|means|how would you|access to)\b"],
#             "patterns_ar": [r"(خطه|نيه|وسيله|كيف.*راح|امكانيه الوصول)"],
#             "gate": "patient_risk_positive",  # only required if patient cues risk
#             "safety_critical": True,
#         },
#         {
#             "id": "summary_next_steps",
#             "desc": "Summarizes + proposes next steps/safety plan/referral.",
#             "weight": 3,
#             "patterns_en": [r"\b(let me summarize|to summarize|what i hear)\b", r"\b(next steps|plan|follow[- ]up|refer|emergency)\b"],
#             "patterns_ar": [r"(خليني الخص|تلخيص|اللي فهمته)", r"(الخطوه القادمه|خطه|متابعه|تحويل|طوارئ)"],
#         },
#     ],
#     "globals": {
#         # very simple MVP mapping; tune later with data
#         "communication_max": 5,
#         "judgment_max": 5,
#     }
# }

# # ----------------------------
# # Patient cue detection (risk)
# # ----------------------------
# PATIENT_RISK_CUES_EN = [r"\b(suicid|kill myself|end my life|self[- ]harm|hurt myself)\b"]
# PATIENT_RISK_CUES_AR = [r"(انتحار|اقتل نفسي|انهي حياتي|ايذاء النفس|اؤذي نفسي)"]

# def patient_risk_positive(patient_msgs: List[str]) -> bool:
#     joined = " ".join(normalize(m) for m in patient_msgs)
#     return any_match(PATIENT_RISK_CUES_EN + PATIENT_RISK_CUES_AR, joined)

# # ----------------------------
# # Main evaluator
# # ----------------------------
# def evaluate_trainee(conversation_history: List[Dict[str, str]], condition: str, language: str) -> Dict[str, Any]:
#     trainee_msgs = [m["content"] for m in conversation_history if m.get("role") == "user"]
#     patient_msgs = [m["content"] for m in conversation_history if m.get("role") == "assistant"]

#     risk_positive = patient_risk_positive(patient_msgs)

#     checklist_results = []
#     total = 0
#     total_possible = 0
#     flags = []

#     for item in RUBRIC["items"]:
#         weight = item["weight"]
#         total_possible += weight

#         # gate logic
#         if item.get("gate") == "patient_risk_positive" and not risk_positive:
#             # not required, treat as N/A (don’t add to possible)
#             total_possible -= weight
#             continue

#         patterns = item["patterns_ar"] if language == "Arabic" else item["patterns_en"]
#         ev = find_evidence(patterns, trainee_msgs)
#         score = weight if ev else 0

#         checklist_results.append({
#             "id": item["id"],
#             "desc": item["desc"],
#             "score": score,
#             "weight": weight,
#             "evidence": ev,
#         })

#         total += score

#         if item.get("safety_critical") and risk_positive and not ev:
#             flags.append({
#                 "type": "SAFETY_CRITICAL",
#                 "id": item["id"],
#                 "message": "Patient risk cue present, but trainee did not assess plan/intent/means/access."
#             })

#     # Global ratings (MVP heuristic)
#     # communication: based on empathy + summary presence
#     empathy = next((x for x in checklist_results if x["id"] == "empathy_validation"), None)
#     summary = next((x for x in checklist_results if x["id"] == "summary_next_steps"), None)
#     comm_raw = (1 if empathy and empathy["score"] > 0 else 0) + (1 if summary and summary["score"] > 0 else 0)
#     communication = min(5, 2 + comm_raw * 1.5)  # 2..5

#     # judgment: based on total % + safety penalty
#     pct = (total / total_possible) if total_possible > 0 else 0.0
#     judgment = 1 + 4 * pct
#     if any(f["type"] == "SAFETY_CRITICAL" for f in flags):
#         judgment = min(judgment, 2)  # cap if unsafe
#     judgment = min(5, max(1, round(judgment)))

#     # pass/fail (tune later)
#     passed = (pct >= 0.7) and not any(f["type"] == "SAFETY_CRITICAL" for f in flags)

#     feedback = []
#     if empathy and empathy["score"] == 0:
#         feedback.append("Add a brief validation/empathy statement when the patient shares distress.")
#     if risk_positive and not any(x["id"] == "risk_depth" and x["score"] > 0 for x in checklist_results):
#         feedback.append("When suicidality/self-harm is mentioned, assess plan/intent/means/access and escalate safety planning.")
#     if summary and summary["score"] == 0:
#         feedback.append("End with a short summary and clear next steps.")

#     return {
#         "condition": condition,
#         "language": language,
#         "checklist": checklist_results,
#         "globals": {"communication": communication, "judgment": judgment},
#         "flags": flags,
#         "total_score": total,
#         "total_possible": total_possible,
#         "percent": round(pct, 3),
#         "pass": passed,
#         "feedback": feedback,
#     }



import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

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
    """Return True if any regex pattern matches the given (already normalized) text."""
    for p in patterns or []:
        if re.search(p, text, flags=re.IGNORECASE):
            return True
    return False

def find_evidence(patterns: List[str], messages: List[str]) -> Optional[str]:
    """Return the first original message that matches any pattern, else None."""
    for m in messages or []:
        nm = normalize(m)
        if any_match(patterns, nm):
            return m
    return None

# ----------------------------
# Rubric loading (JSON)
# ----------------------------
def _default_rubric_path() -> Path:
    """<this_file_dir>/rubrics/psychiatry_intake.json"""
    return Path(__file__).resolve().parent / "rubrics" / "psychiatry_intake.json"

def load_rubric(rubric_path: str) -> Dict[str, Any]:
    """Load and minimally validate a rubric JSON file."""
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
    """Evaluate trainee messages using a JSON rubric (no LLM judge)."""

    if rubric is None:
        rubric_path = rubric_path or str(_default_rubric_path())
        rubric = load_rubric(rubric_path)

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

        checklist_results.append({
            "id": item.get("id"),
            "desc": item.get("desc"),
            "score": score,
            "weight": weight,
            "evidence": ev,
        })
        total += score

        if item.get("safety_critical") and risk_positive and not ev:
            flags.append({
                "type": "SAFETY_CRITICAL",
                "id": item.get("id"),
                "message": "Patient risk cue present, but trainee did not assess plan/intent/means/access."
            })

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
        feedback.append("When suicidality/self-harm is mentioned, assess plan/intent/means/access and escalate safety planning.")
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
