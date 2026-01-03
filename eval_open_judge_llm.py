from pathlib import Path
import sys

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import os
import json
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# -----------------------------
# Groq client (patient sim + trainee judge)
# -----------------------------
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# -----------------------------
# Optional DeepEval imports (patient evaluation)
# -----------------------------
DEEPEVAL_AVAILABLE = True
try:
    from deepeval.test_case import Turn, ConversationalTestCase
    from deepeval.metrics import RoleAdherenceMetric, ConversationalGEval
except Exception:
    DEEPEVAL_AVAILABLE = False

# -----------------------------
# Optional: NEW trainee eval pipeline (Groq judge + deterministic scorer)
# -----------------------------
TRAINEE_LLM_EVAL_AVAILABLE = True
TRAINEE_LLM_IMPORT_ERROR = ""
try:
    from src.trainee_judge.trainee_judge_schema import load_rubric as load_examiner_rubric
    from src.trainee_judge.trainee_judge_groq import judge_trainee_with_groq, GroqJudgeConfig
    from src.trainee_judge.trainee_score import score_from_judge_output
except Exception as e:
    TRAINEE_LLM_EVAL_AVAILABLE = False
    TRAINEE_LLM_IMPORT_ERROR = str(e)
     
# -----------------------------
# Optional: legacy regex trainee evaluation (kept for comparison)
# -----------------------------
TRAINEE_REGEX_EVAL_AVAILABLE = True
try:
    from evaluation_engine import evaluate_trainee as regex_evaluate_trainee
except Exception:
    TRAINEE_REGEX_EVAL_AVAILABLE = False
    regex_evaluate_trainee = None


# -----------------------------
# Helpers
# -----------------------------
def build_system_prompt(condition: str, language: str) -> str:
    return (
        "You are a patient in a psychology clinic.\n"
        f"You suffer from: {condition}.\n\n"
        "You are being interviewed by a psychiatrist who will ask questions about your mental health.\n"
        "Answer only in relevance to your condition. You may mention past events or traumatic experiences if relevant.\n"
        "You must stay in character and not break the fourth wall.\n\n"
        "Constraints:\n"
        "- Answer concisely: max 2 sentences.\n"
        "- If you do not know the answer, say exactly: I don't know.\n"
        "- If the question is not relevant to your condition, say exactly: I don't know.\n"
        "- Do not reveal any information not related to your condition.\n"
        "- Do not reveal that you are an AI language model.\n\n"
        f"Language: respond in {language}.\n"
    )


def init_or_reset_conversation(condition: str, language: str) -> None:
    st.session_state.conversation_history = [
        {"role": "system", "content": build_system_prompt(condition, language)}
    ]
    st.session_state.active_condition = condition
    st.session_state.active_language = language


def generate_patient_response(conversation):
    resp = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=conversation,
        temperature=1,
        max_completion_tokens=8192,
        top_p=1,
        reasoning_effort="medium",
        stream=False,
        stop=None,
    )
    return resp.choices[0].message.content


def history_to_turns_for_deepeval(history):
    turns = []
    for m in history:
        if m.get("role") in ("user", "assistant"):
            turns.append(Turn(role=m["role"], content=m["content"]))
    return turns


def build_chatbot_role(condition: str, language: str) -> str:
    return (
        "You are a simulated patient in a psychology clinic. "
        f"You suffer from {condition}. "
        "Stay in character and do not break the fourth wall. "
        "Answer concisely (max 2 sentences). "
        "If irrelevant or unknown, say exactly: I don't know. "
        "Never mention being an AI. "
        f"Respond in {language}."
    )


def _default_rubric_path() -> str:
    return "rubrics/psychiatry_intake.json"


def conversation_ready() -> bool:
    return bool(st.session_state.get("conversation_history")) and len(st.session_state.conversation_history) >= 2


# -----------------------------
# Session state init
# -----------------------------
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "active_condition" not in st.session_state:
    st.session_state.active_condition = ""
if "active_language" not in st.session_state:
    st.session_state.active_language = "English"

if "rubric_path" not in st.session_state:
    st.session_state.rubric_path = _default_rubric_path()
if "rubric" not in st.session_state:
    st.session_state.rubric = None


# =========================
# UI with Tabs
# =========================
st.set_page_config(page_title="Simulated Patient Chatbot", layout="wide")
st.title("Simulated Patient Chatbot")

tab_chat, tab_patient_eval, tab_trainee_eval = st.tabs(["Chat", "Evaluate Patient", "Evaluate Trainee"])


# -------------------------
# TAB 1: Chat
# -------------------------
with tab_chat:
    condition = st.text_input("Enter the patient's condition (Ex: depression, anxiety):").strip()
    language = st.selectbox("Select the language for responses:", ["English", "Arabic"], index=0)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start / Reset conversation"):
            if not condition:
                st.warning("Please enter a condition first.")
            else:
                init_or_reset_conversation(condition, language)

    with col2:
        if st.button("Clear everything"):
            st.session_state.conversation_history = []
            st.session_state.active_condition = ""
            st.session_state.active_language = "English"
            st.rerun()

    chat_box = st.container(height=520)

    if condition and not st.session_state.conversation_history:
        init_or_reset_conversation(condition, language)

    if st.session_state.conversation_history and condition and (
        condition != st.session_state.active_condition or language != st.session_state.active_language
    ):
        st.info("Condition or language changed. Click **Start / Reset conversation** to apply the new settings.")

    user_message = st.chat_input("Type your message here...")

    if user_message:
        if not st.session_state.conversation_history:
            st.warning("Click Start / Reset conversation first.")
        else:
            st.session_state.conversation_history.append({"role": "user", "content": user_message})
            try:
                assistant_response = generate_patient_response(st.session_state.conversation_history)
                st.session_state.conversation_history.append({"role": "assistant", "content": assistant_response})
            except Exception as e:
                st.error(f"LLM call failed: {e}")

    with chat_box:
        for message in st.session_state.conversation_history:
            if message["role"] == "user":
                st.chat_message("user").markdown(message["content"])
            elif message["role"] == "assistant":
                st.chat_message("assistant").markdown(message["content"])


# -------------------------
# TAB 2: Evaluate Patient (DeepEval)
# -------------------------
with tab_patient_eval:
    st.subheader("Patient evaluation (DeepEval)")

    if not DEEPEVAL_AVAILABLE:
        st.warning("DeepEval not installed. Install with: `pip install -U deepeval`")
    elif not os.getenv("OPENAI_API_KEY"):
        st.warning("OPENAI_API_KEY is missing. Add it to your environment or .env file to enable DeepEval judges.")
    elif not conversation_ready():
        st.info("Not enough turns yet. Have at least one trainee message and one patient reply.")
    else:
        turns = history_to_turns_for_deepeval(st.session_state.conversation_history)

        role_threshold = st.slider("Role adherence threshold", 0.0, 1.0, 0.8, 0.05)
        geval_threshold = st.slider("Conversation quality threshold", 0.0, 1.0, 0.7, 0.05)

        context_list = [
            f"Condition: {st.session_state.active_condition or 'N/A'}",
            f"Language: {st.session_state.active_language or 'N/A'}",
            "Rules: <=2 sentences; irrelevant/unknown -> exactly 'I don't know'; never mention being an AI.",
        ]

        test_case = ConversationalTestCase(
            turns=turns,
            scenario="Psychiatry intake interview: doctor asks questions, simulated patient answers.",
            expected_outcome="Stay in character; <=2 sentences; correct language; 'I don't know' when irrelevant/unknown; never mention AI.",
            chatbot_role=build_chatbot_role(st.session_state.active_condition, st.session_state.active_language),
            context=context_list,
        )

        if st.button("Run patient evaluation"):
            role_metric = RoleAdherenceMetric(threshold=role_threshold, include_reason=True)
            sim_metric = ConversationalGEval(
                name="PatientSimQuality",
                criteria=(
                    "Evaluate the assistant as a simulated patient. Must stay in character, never mention being an AI, "
                    "only discuss information relevant to the condition, respond in the selected language, keep each answer "
                    "to max 2 sentences, and if irrelevant/unknown reply exactly: I don't know."
                ),
                threshold=geval_threshold,
            )

            for metric in (role_metric, sim_metric):
                try:
                    metric.measure(test_case)
                    with st.expander(f"{metric.__class__.__name__} results", expanded=True):
                        st.write("Score:", metric.score)
                        st.write("Threshold:", getattr(metric, "threshold", None))
                        st.write("Passed:", metric.is_successful())
                        st.write("Reason:", getattr(metric, "reason", ""))
                except Exception as e:
                    st.error(f"{metric.__class__.__name__} failed: {e}")


# -------------------------
# TAB 3: Evaluate Trainee (Groq judge + deterministic scorer)
# -------------------------
with tab_trainee_eval:
    st.subheader("Trainee evaluation (Groq judge + deterministic scorer)")
    st.caption("Evaluates the trainee using the full conversation + an examiner-editable rubric JSON.")

    if not os.getenv("GROQ_API_KEY"):
        st.warning("GROQ_API_KEY is missing. Add it to your environment or .env file to enable trainee judging.")
    elif not conversation_ready():
        st.info("Not enough turns yet. Have at least one trainee message and one patient reply.")
    elif not TRAINEE_LLM_EVAL_AVAILABLE:
        st.error("Trainee LLM evaluation modules could not be imported.")
        st.code(TRAINEE_LLM_IMPORT_ERROR or "Unknown import error.")
    else:
        # -------- Rubric controls --------
        st.markdown("### Rubric")
        col_r1, col_r2, col_r3 = st.columns([2, 1, 1])
        with col_r1:
            st.session_state.rubric_path = st.text_input("Rubric JSON path (server)", value=st.session_state.rubric_path)
        with col_r2:
            if st.button("Load / Reload rubric"):
                try:
                    st.session_state.rubric = load_examiner_rubric(st.session_state.rubric_path)
                    st.success("Rubric loaded.")
                except Exception as e:
                    st.session_state.rubric = None
                    st.error(f"Failed to load rubric: {e}")
        with col_r3:
            if st.session_state.rubric is not None:
                st.download_button(
                    "Download rubric",
                    data=json.dumps(st.session_state.rubric, ensure_ascii=False, indent=2),
                    file_name=f"{st.session_state.rubric.get('rubric_id','rubric')}.json",
                    mime="application/json",
                )

        # Auto-load once
        if st.session_state.rubric is None:
            try:
                st.session_state.rubric = load_examiner_rubric(st.session_state.rubric_path)
            except Exception:
                st.session_state.rubric = None

        if st.session_state.rubric is None:
            st.warning("No rubric loaded yet. Fix the path above or load a rubric file.")
        else:
            rb = st.session_state.rubric
            st.info(f"Loaded rubric: **{rb.get('rubric_id','')}** (v{rb.get('version','')}) — items: **{len(rb.get('items', []))}**")

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
                        grade, meta = judge_trainee_with_groq(
                            st.session_state.conversation_history,
                            language=st.session_state.active_language or "English",
                            condition=st.session_state.active_condition or "",
                            rubric=rb,
                            config=config,
                        )
                        scored = score_from_judge_output(
                            st.session_state.conversation_history,
                            rubric=rb,
                            language=st.session_state.active_language or "English",
                            judge_grade=grade,
                        )
                        st.session_state.trainee_grade = grade
                        st.session_state.trainee_meta = meta
                        st.session_state.trainee_scored = scored
                        st.success("Trainee evaluation completed.")
                    except Exception as e:
                        st.error(f"Trainee evaluation failed: {e}")

            with run_col2:
                st.caption("If strict schema fails on a model, uncheck **Strict JSON Schema** (fallback uses JSON object mode).")

            if "trainee_scored" in st.session_state:
                scored = st.session_state.trainee_scored
                grade = st.session_state.trainee_grade
                meta = st.session_state.trainee_meta

                st.markdown("### Results")
                st.metric("Total score", f"{scored['total_score']}/{scored['total_possible']}")
                st.progress(min(1.0, max(0.0, float(scored.get("percent", 0.0)))))
                colA, colB, colC = st.columns(3)
                with colA:
                    st.metric("Percent", f"{round(scored.get('percent', 0.0) * 100, 1)}%")
                with colB:
                    st.metric("Pass", "✅" if scored.get("pass") else "❌")
                with colC:
                    st.metric("Min percent", f"{round(float(scored.get('min_percent', 0.7)) * 100, 1)}%")

                if scored.get("flags"):
                    st.error("Flags")
                    for f in scored["flags"]:
                        st.write(f"- **{f.get('type')}** — {f.get('message')} (item: {f.get('item_id')})")

                with st.expander("Checklist (per item)", expanded=True):
                    rows = []
                    for it in scored.get("items", []):
                        rows.append(
                            {
                                "id": it["id"],
                                "points": f"{it['points_awarded']}/{it['weight']}" if it["included"] else "N/A (gated)",
                                "achieved": it["achieved"],
                                "confidence": it["confidence"],
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

                if TRAINEE_REGEX_EVAL_AVAILABLE:
                    with st.expander("Legacy (regex) evaluation baseline", expanded=False):
                        st.caption("Older regex-based engine (comparison only).")
                        if st.button("Run legacy regex evaluation"):
                            legacy = regex_evaluate_trainee(
                                st.session_state.conversation_history,
                                condition=st.session_state.active_condition or "",
                                language=st.session_state.active_language or "English",
                                rubric_path=st.session_state.rubric_path,
                            )
                            st.code(json.dumps(legacy, ensure_ascii=False, indent=2), language="json")
