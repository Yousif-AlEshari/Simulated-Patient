"""
trainee_judge_schema.py

Builds a Groq Structured Outputs JSON Schema for grading a trainee against an examiner-editable rubric JSON.

Key idea:
- The schema is generated FROM the rubric JSON's items[] list.
- If the examiner adds/removes items, the expected judge output updates automatically.

Groq Structured Outputs expects:
response_format = {"type": "json_schema", "json_schema": {"name": "...", "strict": True, "schema": <JSON Schema dict>}}
"""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any, Dict, List
from dotenv import load_dotenv

DEFAULT_RUBRIC_PATH = Path(__file__).resolve().parent / "rubrics" / "psychiatry_intake.json"
load_dotenv()

def load_rubric(rubric_path: str | Path = DEFAULT_RUBRIC_PATH) -> Dict[str, Any]:
    """Load rubric JSON from disk."""
    path = Path(rubric_path)
    if not path.exists():
        raise FileNotFoundError(f"Rubric not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def rubric_fingerprint(rubric: Dict[str, Any]) -> str:
    """Deterministic SHA-256 hash of the rubric JSON (useful for audit logs)."""
    canonical = json.dumps(rubric, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _item_ids(rubric: Dict[str, Any]) -> List[str]:
    items = rubric.get("items", [])
    if not isinstance(items, list) or not items:
        raise ValueError("Rubric must contain a non-empty 'items' list.")
    ids: List[str] = []
    for i, it in enumerate(items):
        if not isinstance(it, dict) or "id" not in it:
            raise ValueError(f"Rubric item #{i} must be an object with an 'id'.")
        item_id = str(it["id"]).strip()
        if not item_id:
            raise ValueError(f"Rubric item #{i} has an empty 'id'.")
        if item_id in ids:
            raise ValueError(f"Duplicate rubric item id: '{item_id}'")
        ids.append(item_id)
    return ids


def build_judge_output_schema(rubric: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a JSON Schema dict (Draft 2020-12 compatible) describing the judge's output.

    We model item results as an OBJECT keyed by item id:
      item_results: {
         "intro_agenda": {...},
         "risk_screen": {...},
         ...
      }

    This forces the LLM to provide a decision for every rubric item, and prevents extra keys.
    """
    ids = _item_ids(rubric)

    # Schema for each rubric item result
    per_item_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "achieved": {"type": "boolean"},
            "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            "evidence_turns": {
                "type": "array",
                "items": {"type": "integer", "minimum": 1},
                "minItems": 0,
            },
            "rationale": {"type": "string"},
        },
        "required": ["achieved", "confidence", "evidence_turns", "rationale"],
        "additionalProperties": False,
    }

    item_results_properties = {item_id: per_item_schema for item_id in ids}

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "rubric_id": {"type": "string"},
            "rubric_version": {"type": "string"},
            "rubric_fingerprint": {"type": "string"},
            "item_results": {
                "type": "object",
                "properties": item_results_properties,
                "required": ids,
                "additionalProperties": False,
            },
            "flags": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "item_id": {"type": "string"},
                        "message": {"type": "string"},
                        "evidence_turns": {
                            "type": "array",
                            "items": {"type": "integer", "minimum": 1},
                            "minItems": 0,
                        },
                    },
                    "required": ["type", "item_id", "message", "evidence_turns"],
                    "additionalProperties": False,
                },
                "minItems": 0,
            },
            "summary_feedback": {"type": "array", "items": {"type": "string"}, "minItems": 0},
        },
        "required": ["rubric_id", "rubric_version", "rubric_fingerprint", "item_results", "flags", "summary_feedback"],
        "additionalProperties": False,
    }


def build_response_format(
    rubric: Dict[str, Any],
    name: str = "trainee_rubric_grade",
    strict: bool = True,
) -> Dict[str, Any]:
    """Groq response_format payload for Structured Outputs."""
    return {
        "type": "json_schema",
        "json_schema": {
            "name": name,
            "strict": bool(strict),
            "schema": build_judge_output_schema(rubric),
        },
    }


if __name__ == "__main__":
    rb = load_rubric(DEFAULT_RUBRIC_PATH)
    print("rubric_id:", rb.get("rubric_id"))
    print("rubric_version:", rb.get("version"))
    print("rubric_fingerprint:", rubric_fingerprint(rb))
    print(json.dumps(build_judge_output_schema(rb), ensure_ascii=False, indent=2))
