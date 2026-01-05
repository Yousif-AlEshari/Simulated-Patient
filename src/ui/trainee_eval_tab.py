"""src.ui.trainee_eval_tab

Trainee evaluation UI.

Uses:
- LLM judge (Groq) -> structured JSON
- Deterministic scorer -> final score/pass/flags

Optionally shows a legacy regex baseline.
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

import streamlit as st

from src.state.session_keys import (
    ACTIVE_CONDITION,
    ACTIVE_LANGUAGE,
    RUBRIC,
    RUBRIC_PATH,
    TRAINEE_GRADE,
    TRAINEE_META,
    TRAINEE_SCORED,
)
from src.state.session_store import conversation_ready, get_history
from src.trainee_judge.trainee_judge_groq import GroqJudgeConfig


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def render_trainee_eval_tab(*, trainee_pipeline: Any, legacy_regex_evaluator: Optional[Any] = None) -> None:
    st.subheader("Trainee evaluation (LLM judge + deterministic scorer)")
    st.caption("Evaluates the trainee using the full conversation + an examiner-editable rubric JSON.")

    if not os.getenv("GROQ_API_KEY"):
        st.warning("GROQ_API_KEY is missing. Add it to your environment or .env file to enable trainee judging.")
        return

    if not conversation_ready():
        st.info("Not enough turns yet. Have at least one trainee message and one patient reply.")
        return

    # -------- Rubric controls --------
    st.markdown("### Rubric")
    col_r1, col_r2, col_r3 = st.columns([2, 1, 1])

    with col_r1:
        st.session_state[RUBRIC_PATH] = st.text_input("Rubric JSON path (server)", value=st.session_state[RUBRIC_PATH])

    with col_r2:
        if st.button("Load / Reload rubric"):
            try:
                st.session_state[RUBRIC] = trainee_pipeline.load_rubric(st.session_state[RUBRIC_PATH])
                st.success("Rubric loaded.")
            except Exception as e:
                st.session_state[RUBRIC] = None
                st.error(f"Failed to load rubric: {e}")

    with col_r3:
        if st.session_state.get(RUBRIC) is not None:
            rb = st.session_state[RUBRIC]
            st.download_button(
                "Download rubric",
                data=json.dumps(rb, ensure_ascii=False, indent=2),
                file_name=f"{rb.get('rubric_id','rubric')}.json",
                mime="application/json",
            )

    # Auto-load once
    if st.session_state.get(RUBRIC) is None:
        try:
            st.session_state[RUBRIC] = trainee_pipeline.load_rubric(st.session_state[RUBRIC_PATH])
        except Exception:
            st.session_state[RUBRIC] = None

    if st.session_state.get(RUBRIC) is None:
        st.warning("No rubric loaded yet. Fix the path above or load a rubric file.")
        return

    rb = st.session_state[RUBRIC]
    st.info(
        f"Loaded rubric: **{rb.get('rubric_id','')}** (v{rb.get('version','')}) — items: **{len(rb.get('items', []))}**"
    )

    # -------- Judge settings --------
    st.markdown("### Judge settings")
    col_j1, col_j2, col_j3, col_j4 = st.columns(4)

    with col_j1:
        model = st.selectbox("Judge model", ["openai/gpt-oss-120b", "openai/gpt-oss-20b"], index=0)
    with col_j2:
        strict_schema = st.checkbox("Strict JSON Schema", value=True)
    with col_j3:
        seed = st.number_input("Seed (best effort)", min_value=0, max_value=10_000_000, value=42, step=1)
    with col_j4:
        reasoning_effort = st.selectbox("Reasoning effort", ["none", "low", "medium", "high"], index=2)

    config = GroqJudgeConfig(
        model=model,
        temperature=0.0,
        seed=int(seed),
        reasoning_effort=reasoning_effort,
        reasoning_format="hidden",
        max_completion_tokens=1400,
        strict_schema=bool(strict_schema),
    )

    run_col1, run_col2 = st.columns([1, 2])
    with run_col1:
        if st.button("Run trainee evaluation (LLM judge)"):
            try:
                result = trainee_pipeline.run(
                    get_history(),
                    language=st.session_state.get(ACTIVE_LANGUAGE, "English"),
                    condition=st.session_state.get(ACTIVE_CONDITION, ""),
                    rubric=rb,
                    judge_config=config,
                )
                st.session_state[TRAINEE_GRADE] = result.judge_grade
                st.session_state[TRAINEE_META] = result.judge_meta
                st.session_state[TRAINEE_SCORED] = result.scored
                st.success("Trainee evaluation completed.")
            except Exception as e:
                st.error(f"Trainee evaluation failed: {e}")

    with run_col2:
        st.caption("If strict schema fails on a model, uncheck **Strict JSON Schema** (fallback uses JSON object mode).")

    scored = st.session_state.get(TRAINEE_SCORED)
    if not scored:
        return

    grade = st.session_state.get(TRAINEE_GRADE) or {}
    meta = st.session_state.get(TRAINEE_META) or {}

    st.markdown("### Results")
    st.metric("Total score", f"{scored.get('total_score')}/{scored.get('total_possible')}")
    st.progress(min(1.0, max(0.0, _safe_float(scored.get("percent"), 0.0))))

    colA, colB, colC = st.columns(3)
    with colA:
        st.metric("Percent", f"{round(_safe_float(scored.get('percent'), 0.0) * 100, 1)}%")
    with colB:
        st.metric("Pass", "✅" if scored.get("pass") else "❌")
    with colC:
        st.metric("Min percent", f"{round(_safe_float(scored.get('min_percent'), 0.7) * 100, 1)}%")

    if scored.get("flags"):
        st.error("Flags")
        for f in scored["flags"]:
            st.write(f"- **{f.get('type')}** — {f.get('message')} (item: {f.get('item_id')})")

    with st.expander("Checklist (per item)", expanded=True):
        rows = []
        for it in scored.get("items", []):
            rows.append(
                {
                    "id": it.get("id"),
                    "points": f"{it.get('points_awarded')}/{it.get('weight')}" if it.get("included") else "N/A (gated)",
                    "achieved": it.get("achieved"),
                    "confidence": it.get("confidence"),
                    "evidence_turns": ",".join(str(x) for x in it.get("evidence_turns", [])),
                    "rationale": it.get("rationale", ""),
                }
            )
        st.dataframe(rows, use_container_width=True)

    with st.expander("Feedback", expanded=True):
        for tip in scored.get("summary_feedback", []):
            st.write(f"- {tip}")

    with st.expander("Debug / raw outputs", expanded=False):
        st.write("Judge meta:", meta)
        st.write("Judge grade JSON:")
        st.code(json.dumps(grade, ensure_ascii=False, indent=2), language="json")
        st.write("Deterministic scored JSON:")
        st.code(json.dumps(scored, ensure_ascii=False, indent=2), language="json")

        st.download_button(
            "Download scored JSON",
            data=json.dumps(scored, ensure_ascii=False, indent=2),
            file_name="trainee_scored.json",
            mime="application/json",
        )

    if legacy_regex_evaluator is not None:
        with st.expander("Legacy (regex) evaluation baseline", expanded=False):
            st.caption("Older regex-based engine (comparison only).")
            if st.button("Run legacy regex evaluation"):
                legacy = legacy_regex_evaluator(
                    get_history(),
                    condition=st.session_state.get(ACTIVE_CONDITION, ""),
                    language=st.session_state.get(ACTIVE_LANGUAGE, "English"),
                    rubric_path=st.session_state.get(RUBRIC_PATH),
                )
                st.code(json.dumps(legacy, ensure_ascii=False, indent=2), language="json")
