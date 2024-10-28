from openai import OpenAI
import streamlit as st
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access the API key from environment variables
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Set up custom CSS for styling
st.markdown(
    f"""
    <style>
    /* Background and text colors */
    .main {{ background-color: #f2f5f9; }}
    .stMarkdown h1 {{ color: #3662e3; }}

    /* Button styling */
    div.stButton > button {{
        background-color: #4b7ded;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.25rem;
        transition: background-color 0.3s ease;
    }}
    div.stButton > button:hover {{
        background-color: #5791ff;
    }}

    /* Chat message bubbles */
    .st-chat-message-user {{ background-color: #4b7ded; color: white; }}
    .st-chat-message-assistant {{ background-color: #3662e3; color: white; }}

    /* Aligning the Tractian logo */
    .logo-container {{
        display: flex;
        justify-content: center;
        margin-bottom: 2rem;
    }}
    .logo-container img {{
        max-width: 150px;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# Display the Tractian logo at the top
st.markdown(
    '<div class="logo-container"><img src="tractian_logo.png" alt="Tractian Logo"></div>',
    unsafe_allow_html=True
)

# Title and app layout
st.title("ChatGPT-like clone")

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
