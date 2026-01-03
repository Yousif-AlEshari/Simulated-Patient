# import os
# import streamlit as st
# from dotenv import load_dotenv
# from groq import Groq

# load_dotenv()

# # -----------------------------
# # Optional DeepEval imports
# # -----------------------------
# DEEPEVAL_AVAILABLE = True
# try:
#     from deepeval.test_case import Turn, ConversationalTestCase
#     from deepeval.metrics import RoleAdherenceMetric, ConversationalGEval
# except Exception:
#     DEEPEVAL_AVAILABLE = False


# # -----------------------------
# # Groq client
# # -----------------------------
# client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


# # -----------------------------
# # Helpers
# # -----------------------------
# def build_system_prompt(condition: str, language: str) -> str:
#     # Keep aligned with your original intent, but formatted cleanly.
#     return (
#         "You are a patient in a psychology clinic.\n"
#         f"You suffer from: {condition}.\n\n"
#         "You are being interviewed by a psychiatrist who will ask questions about your mental health.\n"
#         "Answer only in relevance to your condition. You may mention past events or traumatic experiences if relevant.\n"
#         "You must stay in character and not break the fourth wall.\n\n"
#         "Constraints:\n"
#         "- Answer concisely: max 2 sentences.\n"
#         "- If you do not know the answer, say exactly: I don't know.\n"
#         "- If the question is not relevant to your condition, say exactly: I don't know.\n"
#         "- Do not reveal any information not related to your condition.\n"
#         "- Do not reveal that you are an AI language model.\n\n"
#         f"Language: respond in {language}.\n"
#     )


# def init_or_reset_conversation(condition: str, language: str) -> None:
#     st.session_state.conversation_history = [
#         {"role": "system", "content": build_system_prompt(condition, language)}
#     ]
#     st.session_state.active_condition = condition
#     st.session_state.active_language = language


# def generate_response(conversation):
#     """
#     Returns assistant message content (string).
#     """
#     resp = client.chat.completions.create(
#         model="openai/gpt-oss-120b",
#         messages=conversation,
#         temperature=1,
#         max_completion_tokens=8192,
#         top_p=1,
#         reasoning_effort="medium",
#         stream=False,
#         stop=None,
#     )
#     return resp.choices[0].message.content


# def history_to_deepeval_turns(history):
#     """
#     DeepEval Turn.role must be Literal["user","assistant"], so exclude system. :contentReference[oaicite:4]{index=4}
#     """
#     turns = []
#     for msg in history:
#         if msg.get("role") in ("user", "assistant"):
#             turns.append(Turn(role=msg["role"], content=msg["content"]))
#     return turns


# def build_chatbot_role(condition: str, language: str) -> str:
#     # Role string used by RoleAdherenceMetric; required by the metric docs. :contentReference[oaicite:5]{index=5}
#     return (
#         "You are a simulated patient in a psychology clinic. "
#         f"You suffer from {condition}. "
#         "Stay in character and never break the fourth wall. "
#         "Answer only information relevant to your condition. "
#         "Keep each answer to max 2 sentences. "
#         "If asked something irrelevant or unknown, reply exactly: I don't know. "
#         "Never mention being an AI. "
#         f"Respond in {language}."
#     )


# # -----------------------------
# # Session state init
# # -----------------------------
# if "conversation_history" not in st.session_state:
#     st.session_state.conversation_history = []

# if "active_condition" not in st.session_state:
#     st.session_state.active_condition = ""

# if "active_language" not in st.session_state:
#     st.session_state.active_language = ""


# # -----------------------------
# # UI
# # -----------------------------
# st.title("Simulated Patient Chatbot")

# st.text_input(
#     "Enter the patient's condition (Ex: depression, anxiety):",
#     key="condition_input",
# )

# language = st.selectbox(
#     "Select the language for responses:",
#     ["English", "Arabic"],
#     key="language_select",
# )

# condition = (st.session_state.get("condition_input") or "").strip()

# col1, col2 = st.columns(2)

# with col1:
#     if st.button("Start / Reset conversation"):
#         if not condition:
#             st.warning("Please enter a condition first.")
#         else:
#             init_or_reset_conversation(condition, language)

# with col2:
#     if st.button("Clear everything"):
#         st.session_state.conversation_history = []
#         st.session_state.active_condition = ""
#         st.session_state.active_language = ""
#         st.session_state.condition_input = ""
#         st.session_state.language_select = "English"
#         st.rerun()

# # Auto-reset if user changes condition/language after starting
# if condition and (
#     condition != st.session_state.active_condition
#     or language != st.session_state.active_language
# ):
#     # Only auto-reset if a conversation already exists (prevents surprise resets on first load)
#     if len(st.session_state.conversation_history) > 0:
#         init_or_reset_conversation(condition, language)

# # Ensure we have a system prompt once condition exists
# if condition and len(st.session_state.conversation_history) == 0:
#     init_or_reset_conversation(condition, language)


# # -----------------------------
# # Chat flow
# # -----------------------------
# user_message = st.chat_input("Type your message here...")

# if user_message:
#     if not condition:
#         st.warning("Enter a condition first to initialize the simulated patient.")
#     else:
#         st.session_state.conversation_history.append({"role": "user", "content": user_message})

#         try:
#             assistant_response = generate_response(st.session_state.conversation_history)
#         except Exception as e:
#             st.error(f"LLM call failed: {e}")
#             assistant_response = None

#         if assistant_response:
#             st.session_state.conversation_history.append(
#                 {"role": "assistant", "content": assistant_response}
#             )

# # Render conversation (skip system)
# for message in st.session_state.conversation_history:
#     if message["role"] == "user":
#         st.chat_message("user").markdown(message["content"])
#     elif message["role"] == "assistant":
#         st.chat_message("assistant").markdown(message["content"])


# # -----------------------------
# # Evaluation (DeepEval)
# # -----------------------------
# st.divider()
# st.subheader("Evaluation (DeepEval)")

# if not DEEPEVAL_AVAILABLE:
#     st.warning(
#         "DeepEval is not installed or failed to import. Install with: pip install -U deepeval"
#     )
# else:
#     # Most DeepEval metrics are LLM-as-a-judge; you must configure a judge provider (commonly OPENAI_API_KEY). :contentReference[oaicite:6]{index=6}
#     if not os.environ.get("OPENAI_API_KEY"):
#         st.info(
#             "DeepEval needs a judge model configured (commonly via OPENAI_API_KEY). "
#             "Add OPENAI_API_KEY to your environment/.env to enable evaluation."
#         )

#     eval_col1, eval_col2 = st.columns(2)
#     with eval_col1:
#         role_threshold = st.slider("Role adherence threshold", 0.0, 1.0, 0.8, 0.05)
#     with eval_col2:
#         geval_threshold = st.slider("Conversational G-Eval threshold", 0.0, 1.0, 0.7, 0.05)

#     if st.button("Evaluate this conversation"):
#         turns = history_to_deepeval_turns(st.session_state.conversation_history)

#         if len(turns) < 2:
#             st.warning("Not enough turns to evaluate. Have at least one user turn and one assistant turn.")
#         else:
#             test_case = ConversationalTestCase(
#                 turns=turns,
#                 scenario="Psychiatry intake interview: doctor asks questions, simulated patient answers.",
#                 expected_outcome=(
#                     "Patient stays in role, answers only relevant mental-health info, "
#                     "keeps answers <= 2 sentences, uses selected language, and says 'I don't know' when appropriate."
#                 ),
#                 chatbot_role=build_chatbot_role(condition, language),  # required for RoleAdherenceMetric :contentReference[oaicite:7]{index=7}
#                 context=[
#                     f"Condition: {condition}",
#                     f"Language: {language}",
#                     "Rules: <= 2 sentences; if irrelevant/unknown -> reply exactly 'I don't know'; never mention being an AI."
#                 ],
#             )
                        
#             metrics = [
#                 RoleAdherenceMetric(
#                     threshold=role_threshold,
#                     include_reason=True,
#                 ),
#                 ConversationalGEval(
#                     name="PatientSimQuality",
#                     criteria=(
#                         "Evaluate the assistant as a simulated patient in a psychiatry clinic. "
#                         "Must stay in character, never mention being an AI, "
#                         "only discuss information relevant to the given condition, "
#                         "respond in the selected language, "
#                         "keep each answer to max 2 sentences, "
#                         "and if asked something irrelevant or unknown, reply exactly: I don't know."
#                     ),
#                     threshold=geval_threshold,
#                     model="gpt-4o-mini",  # important to avoid logprobs issues
#                 )
#             ]

#             for metric in metrics:
#                 try:
#                     metric.measure(test_case)  # docs show metric.measure(...) for standalone usage :contentReference[oaicite:8]{index=8}
#                     threshold = getattr(metric, "threshold", None)
#                     passed = (metric.score >= threshold) if threshold is not None else None

#                     with st.expander(f"{metric.__class__.__name__} results", expanded=True):
#                         st.write("Score:", metric.score)
#                         if threshold is not None:
#                             st.write("Threshold:", threshold)
#                             st.write("Passed:", passed)
#                         st.write("Reason:", getattr(metric, "reason", ""))
#                 except Exception as e:
#                     st.error(f"{metric.__class__.__name__} failed: {e}")

###############################################################################
import os
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
try:
    from evaluation_engine import evaluate_trainee
    TRAINEE_EVAL_AVAILABLE = True
except Exception:
    evaluate_trainee = None
    TRAINEE_EVAL_AVAILABLE = False
load_dotenv()

# -------- Optional DeepEval imports (so app still runs without it) --------
DEEPEVAL_AVAILABLE = True
try:
    from deepeval.test_case import Turn, ConversationalTestCase
    from deepeval.metrics import RoleAdherenceMetric, ConversationalGEval
except Exception:
    DEEPEVAL_AVAILABLE = False

# -------- Groq client (inference) --------
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# -------- Session state init --------
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

if "active_condition" not in st.session_state:
    st.session_state.active_condition = ""

if "active_language" not in st.session_state:
    st.session_state.active_language = ""


# -------- Helpers --------
def build_system_prompt(condition: str, language: str) -> str:
    return (
        f"You are a patient in a psychology clinic, you suffer from {condition},\n"
        "and you are being interviewed with a psychiatrist who will ask you questions about your \n"
        "mental health and state. You answer about your mental health only in relevance to your condition, "
        "you may bring past events or traumatic experiences to let the doctor know more about your condition. "
        "You must stay in character and not break the fourth wall.\n"
        "You must answer in a concise manner, with answers no longer than 2 sentences.\n"
        "If you do not know the answer, you must say 'I don't know'.\n"
        "If the question is not relevant to your condition, you must say 'I don't know'.\n"
        "You must not reveal any information about yourself that is not related to your condition.\n"
        "You must not reveal that you are an AI language model.\n"
        f"You answer the doctor with {language} language."
    )

def init_or_reset_conversation(condition: str, language: str) -> None:
    st.session_state.conversation_history = [
        {"role": "system", "content": build_system_prompt(condition, language)}
    ]
    st.session_state.active_condition = condition
    st.session_state.active_language = language

def generate_response(conversation):
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
    # DeepEval multi-turn uses Turn(role="user"/"assistant", content="...") :contentReference[oaicite:2]{index=2}
    turns = []
    for m in history:
        if m.get("role") in ("user", "assistant"):
            turns.append(Turn(role=m["role"], content=m["content"]))
    return turns

def build_chatbot_role(condition: str, language: str) -> str:
    # Role string used by Role Adherence metric :contentReference[oaicite:3]{index=3}
    return (
        "You are a simulated patient in a psychology clinic. "
        f"You suffer from {condition}. "
        "Stay in character and do not break the fourth wall. "
        "Answer concisely (max 2 sentences). "
        "If irrelevant or unknown, say exactly: I don't know. "
        "Never mention being an AI. "
        f"Respond in {language}."
    )


# =========================
# UI with Tabs
# =========================
st.title("Simulated Patient Chatbot")

tab_chat, tab_eval, tab_trainee = st.tabs(["Chat", "Evaluate", "Evaluate_trainee"])  # tabs are official Streamlit layout feature :contentReference[oaicite:4]{index=4}

# -------------------------
# TAB 1: Chat
# -------------------------
with tab_chat:
    condition = st.text_input("Enter the patient's condition (Ex: depression, anxiety):").strip()
    language = st.selectbox("Select the language for responses:", ["English", "Arabic"])

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
            st.rerun()
    # --- Reserve a scrolling area for chat messages (stays above the input) ---
    chat_box = st.container(height=500)  # adjust height as you like

    # If user typed condition but hasn't started yet, initialize once
    if condition and not st.session_state.conversation_history:
        init_or_reset_conversation(condition, language)

    # If condition/language changed after start, warn user to reset (no surprise auto-reset)
    if st.session_state.conversation_history and condition and (
        condition != st.session_state.active_condition or language != st.session_state.active_language
    ):
        st.info("Condition or language changed. Click **Start / Reset conversation** to apply the new settings.")

    # --- Put chat_input AFTER the chat_box so it stays at the bottom ---
    user_message = st.chat_input("Type your message here...")

    if user_message:
        if not st.session_state.conversation_history:
            st.warning("Click Start / Reset conversation first.")
        else:
            st.session_state.conversation_history.append({"role": "user", "content": user_message})
            try:
                assistant_response = generate_response(st.session_state.conversation_history)
                st.session_state.conversation_history.append({"role": "assistant", "content": assistant_response})
            except Exception as e:
                st.error(f"LLM call failed: {e}")

    # --- Render chat INSIDE the reserved container (so it appears above the input) ---
    with chat_box:
        for message in st.session_state.conversation_history:
            if message["role"] == "user":
                st.chat_message("user").markdown(message["content"])
            elif message["role"] == "assistant":
                st.chat_message("assistant").markdown(message["content"])

# # -------------------------
# # TAB 2: Evaluate
# # -------------------------
# with tab_eval:
#     st.subheader("Evaluation (DeepEval)")

#     if not DEEPEVAL_AVAILABLE:
#         st.warning("DeepEval not installed. Install with: `pip install -U deepeval`")
#         st.stop()

#     # DeepEval metrics are LLM-as-a-judge; using OpenAI requires OPENAI_API_KEY set :contentReference[oaicite:5]{index=5}
#     if not os.getenv("OPENAI_API_KEY"):
#         st.warning("OPENAI_API_KEY is missing. Add it to your environment or .env file.")
#         st.stop()

#     turns = history_to_turns_for_deepeval(st.session_state.conversation_history)

#     if len(turns) < 2:
#         st.info("Not enough turns to evaluate yet. Have at least one user message and one assistant reply.")
#         st.stop()

#     role_threshold = st.slider("Role adherence threshold", 0.0, 1.0, 0.8, 0.05)
#     geval_threshold = st.slider("Conversation quality threshold", 0.0, 1.0, 0.7, 0.05)

#     # Context must be None or list[str] (NOT a single string) :contentReference[oaicite:6]{index=6}
#     context_list = [
#         f"Condition: {st.session_state.active_condition or 'N/A'}",
#         f"Language: {st.session_state.active_language or 'N/A'}",
#         "Rules: <=2 sentences; irrelevant/unknown -> exactly 'I don't know'; never mention being an AI."
#     ]

#     test_case = ConversationalTestCase(
#         turns=turns,
#         scenario="Psychiatry intake interview: doctor asks questions, simulated patient answers.",
#         expected_outcome="Stay in character; <=2 sentences; correct language; 'I don't know' when irrelevant/unknown; never mention AI.",
#         chatbot_role=build_chatbot_role(st.session_state.active_condition, st.session_state.active_language),
#         context=context_list,
#     )

#     if st.button("Run evaluation"):
#         # Role Adherence: made for role-playing consistency :contentReference[oaicite:7]{index=7}
#         role_metric = RoleAdherenceMetric(threshold=role_threshold, include_reason=True)

#         # Conversational G-Eval: evaluates entire conversation against your criteria :contentReference[oaicite:8]{index=8}
#         # It uses logprobs in some setups; OpenAI supports logprobs in Chat Completions (see cookbook). :contentReference[oaicite:9]{index=9}
#         sim_metric = ConversationalGEval(
#             name="PatientSimQuality",
#             criteria=(
#                 "Evaluate the assistant as a simulated patient. Must stay in character, never mention being an AI, "
#                 "only discuss information relevant to the condition, respond in the selected language, keep each answer "
#                 "to max 2 sentences, and if irrelevant/unknown reply exactly: I don't know."
#             ),
#             threshold=geval_threshold,
#             # If you hit any model-specific issues, set an explicit judge model here:
#             # model="gpt-4o-mini"
#         )

#         metrics = [role_metric, sim_metric]

#         for m in metrics:
#             try:
#                 m.measure(test_case)
#                 with st.expander(f"{m.__class__.__name__} results", expanded=True):
#                     st.write("Score:", m.score)
#                     st.write("Threshold:", getattr(m, "threshold", None))
#                     st.write("Passed:", m.is_successful())
#                     st.write("Reason:", getattr(m, "reason", ""))
#             except Exception as e:
#                 st.error(f"{m.__class__.__name__} failed: {e}")


# -------------------------
# TAB 3: Evaluate_trainee
# -------------------------

# with tab_trainee:
#     st.subheader("Evaluation")

#     eval_tab_trainee, eval_tab_patient = st.tabs(["Trainee (Rubric)", "Patient (DeepEval)"])

    # =========================
    # Trainee evaluation (NO LLM judge)
    # =========================
with tab_trainee:
    st.markdown("Scores the **trainee (user)** messages using your rubric engine (checklist + global ratings).")

    if not TRAINEE_EVAL_AVAILABLE:
        st.error("Couldn't import `evaluate_trainee`. Make sure `trainee_eval_engine.py` is in the same folder as this file.")
        st.stop()

    if not st.session_state.conversation_history or len(st.session_state.conversation_history) < 2:
        st.info("Not enough turns yet. Have at least one trainee message and one patient reply.")
        st.stop()

    from evaluation_engine import load_rubric
    st.session_state.rubric = load_rubric("rubrics/psychiatry_intake.json")
    
    if st.button("Run trainee evaluation"):
        st.session_state.trainee_eval = evaluate_trainee(
            st.session_state.conversation_history,
            condition=st.session_state.active_condition or "",
            language=st.session_state.active_language or "English",
        )

    if st.button("Reload rubric from file"):
        st.session_state.rubric = load_rubric("rubrics/psychiatry_intake.json")
        st.success("Rubric reloaded.")

    # Show latest results (if already run)
    if "trainee_eval" in st.session_state:
        e = st.session_state.trainee_eval

        st.metric("Total score", f'{e["total_score"]}/{e["total_possible"]}')
        st.progress(min(1.0, max(0.0, e.get("percent", 0.0))))
        colA, colB, colC = st.columns(3)
        with colA:
            st.metric("Communication (1–5)", e["globals"]["communication"])
        with colB:
            st.metric("Judgment (1–5)", e["globals"]["judgment"])
        with colC:
            st.metric("Pass", "✅" if e.get("pass") else "❌")

        if e.get("flags"):
            st.error("Safety flags")
            for f in e["flags"]:
                st.write(f"- {f['message']}")

        with st.expander("Checklist (with evidence)", expanded=False):
            for it in e["checklist"]:
                st.write(f"**{it['id']}** — {it['score']}/{it['weight']}")
                if it.get("evidence"):
                    st.caption(it["evidence"])

        if e.get("feedback"):
            with st.expander("Feedback", expanded=True):
                for tip in e["feedback"]:
                    st.write(f"- {tip}")
    else:
        st.info("Click **Run trainee evaluation** to generate scores.")

# =========================
# Patient evaluation (DeepEval; LLM-as-judge)
# =========================
with tab_eval:
    st.subheader("Evaluation (DeepEval)")

    if not DEEPEVAL_AVAILABLE:
        st.warning("DeepEval not installed. Install with: `pip install -U deepeval`")
        st.stop()

    # DeepEval metrics are LLM-as-a-judge; using OpenAI requires OPENAI_API_KEY set :contentReference[oaicite:5]{index=5}
    if not os.getenv("OPENAI_API_KEY"):
        st.warning("OPENAI_API_KEY is missing. Add it to your environment or .env file.")
        st.stop()

    turns = history_to_turns_for_deepeval(st.session_state.conversation_history)

    if len(turns) < 2:
        st.info("Not enough turns to evaluate yet. Have at least one user message and one assistant reply.")
        st.stop()

    role_threshold = st.slider("Role adherence threshold", 0.0, 1.0, 0.8, 0.05)
    geval_threshold = st.slider("Conversation quality threshold", 0.0, 1.0, 0.7, 0.05)

    # Context must be None or list[str] (NOT a single string) :contentReference[oaicite:6]{index=6}
    context_list = [
        f"Condition: {st.session_state.active_condition or 'N/A'}",
        f"Language: {st.session_state.active_language or 'N/A'}",
        "Rules: <=2 sentences; irrelevant/unknown -> exactly 'I don't know'; never mention being an AI."
    ]

    test_case = ConversationalTestCase(
        turns=turns,
        scenario="Psychiatry intake interview: doctor asks questions, simulated patient answers.",
        expected_outcome="Stay in character; <=2 sentences; correct language; 'I don't know' when irrelevant/unknown; never mention AI.",
        chatbot_role=build_chatbot_role(st.session_state.active_condition, st.session_state.active_language),
        context=context_list,
    )

    if st.button("Run evaluation"):
        # Role Adherence: made for role-playing consistency :contentReference[oaicite:7]{index=7}
        role_metric = RoleAdherenceMetric(threshold=role_threshold, include_reason=True)

        # Conversational G-Eval: evaluates entire conversation against your criteria :contentReference[oaicite:8]{index=8}
        # It uses logprobs in some setups; OpenAI supports logprobs in Chat Completions (see cookbook). :contentReference[oaicite:9]{index=9}
        sim_metric = ConversationalGEval(
            name="PatientSimQuality",
            criteria=(
                "Evaluate the assistant as a simulated patient. Must stay in character, never mention being an AI, "
                "only discuss information relevant to the condition, respond in the selected language, keep each answer "
                "to max 2 sentences, and if irrelevant/unknown reply exactly: I don't know."
            ),
            threshold=geval_threshold,
            # If you hit any model-specific issues, set an explicit judge model here:
            # model="gpt-4o-mini"
        )

        metrics = [role_metric, sim_metric]

        for m in metrics:
            try:
                m.measure(test_case)
                with st.expander(f"{m.__class__.__name__} results", expanded=True):
                    st.write("Score:", m.score)
                    st.write("Threshold:", getattr(m, "threshold", None))
                    st.write("Passed:", m.is_successful())
                    st.write("Reason:", getattr(m, "reason", ""))
            except Exception as e:
                st.error(f"{m.__class__.__name__} failed: {e}")

