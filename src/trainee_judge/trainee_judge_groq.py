"""
trainee_judge_groq.py

Calls Groq to grade a trainee conversation against an examiner-editable rubric JSON,
returning STRICT structured JSON (when supported) plus response metadata.

Depends on:
  - trainee_judge_schema.py (build_response_format, load_rubric, rubric_fingerprint)

Groq docs used by this file:
  - Chat Completions parameters: response_format (json_schema/json_object), seed, temperature, reasoning_effort/format
  - Structured Outputs strict mode requirements (required fields + additionalProperties:false)

"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv
from groq import Groq

from .trainee_judge_schema import (
    load_rubric,
    build_response_format,
    rubric_fingerprint,
)

load_dotenv()


# ----------------------------
# Config
# ----------------------------
@dataclass(frozen=True)
class GroqJudgeConfig:
    model: str = "openai/gpt-oss-120b"
    temperature: float = 0.0
    seed: Optional[int] = 42
    reasoning_effort: Optional[str] = "medium"   # GPT-OSS supports low/medium/high
    reasoning_format: Optional[str] = "hidden"   # keep reasoning out of user-visible output
    max_completion_tokens: int = 1200
    strict_schema: bool = True                  # try strict json_schema mode first
    timeout_s: Optional[float] = None           # pass-through if your groq client supports it


# ----------------------------
# Transcript formatting
# ----------------------------
def build_numbered_turns(conversation_history: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Convert your app's conversation history to numbered turns.

    Expected input: [{"role": "user"|"assistant", "content": "..."}]
    Output: [{"turn": 1, "role": "trainee"|"patient", "content": "..."}]
    """
    turns: List[Dict[str, Any]] = []
    t = 1
    for m in conversation_history or []:
        role = m.get("role")
        if role not in ("user", "assistant"):
            continue
        turns.append(
            {
                "turn": t,
                "role": "trainee" if role == "user" else "patient",
                "content": m.get("content", "") or "",
            }
        )
        t += 1
    return turns


def _rubric_for_judge(rubric: Dict[str, Any]) -> Dict[str, Any]:
    """
    Minimize rubric payload sent to the model.

    Keep:
      - ids, descriptions, weights
      - gate + safety_critical
      - optional anchors (if you add them to your JSON)
      - pass_criteria (for context; scoring remains deterministic later)
    """
    items_out = []
    for it in rubric.get("items", []) or []:
        items_out.append(
            {
                "id": it.get("id"),
                "desc": it.get("desc"),
                "weight": it.get("weight", 0),
                "gate": it.get("gate", None),
                "safety_critical": bool(it.get("safety_critical", False)),
                "anchors": it.get("anchors", None),
            }
        )

    return {
        "rubric_id": rubric.get("rubric_id", ""),
        "rubric_version": rubric.get("version", ""),
        "rubric_fingerprint": rubric_fingerprint(rubric),
        "items": items_out,
        "pass_criteria": rubric.get("pass_criteria", {}),
    }


# ----------------------------
# Prompting
# ----------------------------
def build_messages(
    rubric: Dict[str, Any],
    turns: List[Dict[str, Any]],
    language: str,
    condition: Optional[str] = None,
) -> List[Dict[str, str]]:
    """
    Builds the messages payload for the judge model.

    The user message is a JSON object containing:
      - rubric (minimized)
      - conversation turns
      - language/condition context

    Using JSON in the user message makes it easier to parse and reduces ambiguity.
    """
    rb = _rubric_for_judge(rubric)

    system = (
        "You are a strict psychiatry OSCE examiner grading a trainee.\n"
        "Use ONLY the provided conversation turns as evidence. Do NOT assume unstated facts.\n"
        "Grade each rubric item independently.\n"
        "If an item is partially met or unclear, set achieved=false and explain why.\n"
        "When achieved=true, include evidence_turns that support it.\n"
        "Return only the JSON that matches the provided schema."
    )

    user_payload = {
        "language": language,
        "condition": condition,
        "rubric": rb,
        "conversation_turns": turns,
        "grading_instructions": {
            "evidence": "Use turn numbers. Prefer trainee turns, but you may cite patient turns for context (e.g., risk cue).",
            "achieved_definition": "Achieved if the trainee clearly demonstrates the behavior at least once in the conversation.",
        },
    }

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
    ]


# ----------------------------
# Calling Groq
# ----------------------------
def judge_trainee_with_groq(
    conversation_history: List[Dict[str, str]],
    language: str,
    condition: Optional[str] = None,
    rubric_path: Optional[str] = None,
    rubric: Optional[Dict[str, Any]] = None,
    config: GroqJudgeConfig = GroqJudgeConfig(),
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Returns: (grade_json, meta)

    grade_json conforms to the schema produced by build_response_format(rubric).
    meta includes Groq response metadata (model, system_fingerprint, usage).
    """
    client = Groq()

    rb = rubric or load_rubric(rubric_path)  # rubric_path can be None if rubric dict provided
    turns = build_numbered_turns(conversation_history)
    messages = build_messages(rb, turns, language=language, condition=condition)

    # Prefer strict schema when supported; fallback to json_object mode if strict fails.
    response_format = build_response_format(rb, strict=config.strict_schema) if config.strict_schema else {"type": "json_object"}

    try:
        resp = client.chat.completions.create(
            model=config.model,
            messages=messages,
            temperature=config.temperature,
            seed=config.seed,
            response_format=response_format,
            reasoning_effort=config.reasoning_effort,
            reasoning_format=config.reasoning_format,
            max_completion_tokens=config.max_completion_tokens,
        )
    except Exception as e:
        # If strict schema isn't supported by the model, Groq docs note you may get 400 errors.
        # Fall back to json_object mode (valid JSON, but not guaranteed schema adherence).
        if config.strict_schema:
            resp = client.chat.completions.create(
                model=config.model,
                messages=messages,
                temperature=config.temperature,
                seed=config.seed,
                response_format={"type": "json_object"},
                reasoning_effort=config.reasoning_effort,
                reasoning_format=config.reasoning_format,
                max_completion_tokens=config.max_completion_tokens,
            )
        else:
            raise

    content = resp.choices[0].message.content
    grade = json.loads(content)

    # Minimal sanity checks (even if strict mode is on, these help catch integration bugs)
    expected_fp = rubric_fingerprint(rb)
    if grade.get("rubric_fingerprint") != expected_fp:
        # Don't fail hard; stamp the real fingerprint so downstream logs are accurate.
        grade["rubric_fingerprint"] = expected_fp
    if grade.get("rubric_id") != rb.get("rubric_id", ""):
        grade["rubric_id"] = rb.get("rubric_id", "")
    if grade.get("rubric_version") != rb.get("version", ""):
        grade["rubric_version"] = rb.get("version", "")

    meta = {
        "model": getattr(resp, "model", None),
        "system_fingerprint": getattr(resp, "system_fingerprint", None),
        "usage": getattr(resp, "usage", None),
        "seed": config.seed,
        "temperature": config.temperature,
        "strict_schema": config.strict_schema,
    }
    return grade, meta


if __name__ == "__main__":
    # Minimal manual test: run this file and it will grade a tiny hardcoded transcript.
    demo_history = [
        {"role": "user", "content": "Hello, I'm Dr. Mike. What brings you here today?"},
        {"role": "assistant", "content": "I've been feeling low and can't sleep."},
        {"role": "user", "content": "I'm sorry to hear that. Have you had thoughts of harming yourself?"},
        {"role": "assistant", "content": "No."},
    ]
    grade, meta = judge_trainee_with_groq(
        demo_history,
        language="English",
        condition="depression",
        rubric_path="rubrics/psychiatry_intake.json",
    )
    print(json.dumps({"meta": meta, "grade": grade}, ensure_ascii=False, indent=2))
