from openai import OpenAI
import streamlit as st
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access the API key from environment variables
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

st.image("images/tractian_logo.png", width=150)

# Title and app layout
st.title("Chatbot Tractian")

# Markdown text for simple explanation of how to use (text in portuguese)
st.markdown(
    """
    Este é um chatbot que utiliza a API de linguagem natural da OpenAI para responder perguntas. 
    Você pode conversar com ele e fazer perguntas sobre a Tractian, nossa plataforma e como podemos te ajudar.
    """,
    unsafe_allow_html=True
)

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})
