import os
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# -----------------------------
# Optional DeepEval imports
# -----------------------------
DEEPEVAL_AVAILABLE = True
try:
    from deepeval.test_case import Turn, ConversationalTestCase
    from deepeval.metrics import RoleAdherenceMetric, ConversationalGEval
    from deepeval.models import GPTModel
except Exception:
    DEEPEVAL_AVAILABLE = False


# -----------------------------
# Groq client
# -----------------------------
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

GROQ_BASE_URL = "https://api.groq.com/openai/v1"

judge_model = GPTModel(
    model="openai/gpt-oss-120b",               # must be a Groq-available model id :contentReference[oaicite:4]{index=4}
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url=GROQ_BASE_URL,                    # custom provider endpoint :contentReference[oaicite:5]{index=5}
    temperature=0,
    # If DeepEval doesn't have pricing metadata for this model name, set costs to avoid runtime errors :contentReference[oaicite:6]{index=6}
    cost_per_input_token=0,
    cost_per_output_token=0,
)


# -----------------------------
# Helpers
# -----------------------------
def build_system_prompt(condition: str, language: str) -> str:
    # Keep aligned with your original intent, but formatted cleanly.
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


def generate_response(conversation):
    """
    Returns assistant message content (string).
    """
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


def history_to_deepeval_turns(history):
    """
    DeepEval Turn.role must be Literal["user","assistant"], so exclude system. :contentReference[oaicite:4]{index=4}
    """
    turns = []
    for msg in history:
        if msg.get("role") in ("user", "assistant"):
            turns.append(Turn(role=msg["role"], content=msg["content"]))
    return turns


def build_chatbot_role(condition: str, language: str) -> str:
    # Role string used by RoleAdherenceMetric; required by the metric docs. :contentReference[oaicite:5]{index=5}
    return (
        "You are a simulated patient in a psychology clinic. "
        f"You suffer from {condition}. "
        "Stay in character and never break the fourth wall. "
        "Answer only information relevant to your condition. "
        "Keep each answer to max 2 sentences. "
        "If asked something irrelevant or unknown, reply exactly: I don't know. "
        "Never mention being an AI. "
        f"Respond in {language}."
    )


# -----------------------------
# Session state init
# -----------------------------
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

if "active_condition" not in st.session_state:
    st.session_state.active_condition = ""

if "active_language" not in st.session_state:
    st.session_state.active_language = ""


# -----------------------------
# UI
# -----------------------------
st.title("Simulated Patient Chatbot")

st.text_input(
    "Enter the patient's condition (Ex: depression, anxiety):",
    key="condition_input",
)

language = st.selectbox(
    "Select the language for responses:",
    ["English", "Arabic"],
    key="language_select",
)

condition = (st.session_state.get("condition_input") or "").strip()

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
        st.session_state.active_language = ""
        st.session_state.condition_input = ""
        st.session_state.language_select = "English"
        st.rerun()

# Auto-reset if user changes condition/language after starting
if condition and (
    condition != st.session_state.active_condition
    or language != st.session_state.active_language
):
    # Only auto-reset if a conversation already exists (prevents surprise resets on first load)
    if len(st.session_state.conversation_history) > 0:
        init_or_reset_conversation(condition, language)

# Ensure we have a system prompt once condition exists
if condition and len(st.session_state.conversation_history) == 0:
    init_or_reset_conversation(condition, language)


# -----------------------------
# Chat flow
# -----------------------------
user_message = st.chat_input("Type your message here...")

if user_message:
    if not condition:
        st.warning("Enter a condition first to initialize the simulated patient.")
    else:
        st.session_state.conversation_history.append({"role": "user", "content": user_message})

        try:
            assistant_response = generate_response(st.session_state.conversation_history)
        except Exception as e:
            st.error(f"LLM call failed: {e}")
            assistant_response = None

        if assistant_response:
            st.session_state.conversation_history.append(
                {"role": "assistant", "content": assistant_response}
            )

# Render conversation (skip system)
for message in st.session_state.conversation_history:
    if message["role"] == "user":
        st.chat_message("user").markdown(message["content"])
    elif message["role"] == "assistant":
        st.chat_message("assistant").markdown(message["content"])


# -----------------------------
# Evaluation (DeepEval)
# -----------------------------
st.divider()
st.subheader("Evaluation (DeepEval)")

if not DEEPEVAL_AVAILABLE:
    st.warning(
        "DeepEval is not installed or failed to import. Install with: pip install -U deepeval"
    )
else:
    # Most DeepEval metrics are LLM-as-a-judge; you must configure a judge provider (commonly OPENAI_API_KEY). :contentReference[oaicite:6]{index=6}
    if not os.environ.get("GROQ_API_KEY"):
        st.info(
            "DeepEval needs a judge model configured (commonly via OPENAI_API_KEY). "
            "Add OPENAI_API_KEY to your environment/.env to enable evaluation."
        )

    eval_col1, eval_col2 = st.columns(2)
    with eval_col1:
        role_threshold = st.slider("Role adherence threshold", 0.0, 1.0, 0.8, 0.05)
    with eval_col2:
        geval_threshold = st.slider("Conversational G-Eval threshold", 0.0, 1.0, 0.7, 0.05)

    if st.button("Evaluate this conversation"):
        turns = history_to_deepeval_turns(st.session_state.conversation_history)

        if len(turns) < 2:
            st.warning("Not enough turns to evaluate. Have at least one user turn and one assistant turn.")
        else:
            test_case = ConversationalTestCase(
                turns=turns,
                scenario="Psychiatry intake interview: doctor asks questions, simulated patient answers.",
                expected_outcome=(
                    "Patient stays in role, answers only relevant mental-health info, "
                    "keeps answers <= 2 sentences, uses selected language, and says 'I don't know' when appropriate."
                ),
                chatbot_role=build_chatbot_role(condition, language),
                context=[
                    f"Condition: {condition}",
                    f"Language: {language}",
                    "Rules: <= 2 sentences; if irrelevant/unknown -> reply exactly 'I don't know'; never mention being an AI."
                ],
            )

            metrics = [
                RoleAdherenceMetric(threshold=role_threshold, include_reason=True, model=judge_model),
                ConversationalGEval(
                    name="PatientSimQuality",
                    criteria=(
                        "Evaluate the assistant as a simulated patient in a psychiatry clinic. "
                        "Must stay in character, never mention being an AI, "
                        "only discuss information relevant to the given condition, "
                        "respond in the selected language, "
                        "keep each answer to max 2 sentences, "
                        "and if asked something irrelevant or unknown, reply exactly: I don't know."
                        "Eevaluate how the assistant stays in character and follows these constraints."
                        "Evaluate how well the assistant adheres to these requirements."
                    ),
                    threshold=geval_threshold,
                    model=judge_model,
                ),
            ]

            for metric in metrics:
                try:
                    metric.measure(test_case)  # docs show metric.measure(...) for standalone usage :contentReference[oaicite:8]{index=8}
                    threshold = getattr(metric, "threshold", None)
                    passed = (metric.score >= threshold) if threshold is not None else None

                    with st.expander(f"{metric.__class__.__name__} results", expanded=True):
                        st.write("Score:", metric.score)
                        if threshold is not None:
                            st.write("Threshold:", threshold)
                            st.write("Passed:", passed)
                        st.write("Reason:", getattr(metric, "reason", ""))
                except Exception as e:
                    st.error(f"{metric.__class__.__name__} failed: {e}")
