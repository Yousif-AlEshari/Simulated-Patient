import streamlit as st
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

st.title("Simulated Patient Chatbot")
condition = st.text_input("Enter the patient's condition (Ex: depression, anxiety):")
radio_options = ["English", "Arabic"]
language = st.selectbox("Select the language for responses:", radio_options)

if condition and language:
    st.session_state.conversation_history.append(
        {
            "role": "system",
            "content": f"You are a patient in a psychology clinic, you suffer from {condition},\n"
                       f"and you are being interviewed with a psychiatrist who will ask you questions about your \n"
                       "mental health and state. You answer about your mental health only in relevance to your condition, "
                       "you may bring past events or traumatic experiences to let the doctor know more about your condition. "
                       "You must stay in character and not break the fourth wall.\n"
                       "You must answer in a concise manner, with answers no longer than 2 sentences.\n"
                       "If you do not know the answer, you must say 'I don't know'.\n"
                       "If the question is not relevant to your condition, you must say 'I don't know'."
                       " You must not reveal any information about yourself that is not related to your condition.\n"
                       "You must not reveal that you are an AI language model.\n"
                       f"You answer the doctor with {language} language."
        }
    )

def generate_response(conversation):
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=conversation, #Use Passed Conversation History
        temperature=1,
        max_completion_tokens=8192,
        top_p=1,
        reasoning_effort="medium",
        stream=False,
        stop=None
    )
    return response

#User message input field
user_message = st.chat_input("Type your message here...")
if user_message:
    st.session_state.conversation_history.append({"role": "user", "content": user_message})

    # st.chat_message("user").markdown(user_message)


    response = generate_response(st.session_state.conversation_history)
    # st.write(response) # Used for debugging
    
    assistant_response = response.choices[0].message.content
    

    # st.chat_message("assistant").markdown(assistant_response)
    st.session_state.conversation_history.append({"role": "assistant", "content": assistant_response})

for message in st.session_state.conversation_history:
    if message["role"] == "user":
        st.chat_message("user").markdown(message["content"])
    elif message["role"] == "assistant":
        st.chat_message("assistant").markdown(message["content"])
