import requests
import uuid
import streamlit as st
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Set Tractian blue color
tractian_blue = "#3662e3"

st.image("images/tractian_logo_name.png", width=120)

# Title and app layout
st.title("Chatbot Tractian")

# Introduction text
st.markdown(
    f"""
    <p>
    Este é um chatbot que utiliza uma API para responder perguntas sobre a Tractian, nossa plataforma e como podemos te ajudar.
    </p>
    """,
    unsafe_allow_html=True
)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

if prompt := st.chat_input("Qual sua dúvida?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate a unique conversation ID
    conversation_id = str(uuid.uuid4())

    # Prepare payload for the backend request
    payload = {
        "prompt": prompt,
        "conversation_id": conversation_id
    }

    # Send request to the backend
    response = requests.post("http://localhost:5001/consulta", json=payload)

    if response.status_code == 200:
        # Parse the response JSON
        response_data = response.json()

        # Check if all expected keys are present
        if all(key in response_data for key in ["date", "common_hours", "found_pieces", "unmatched_pieces"]):
            # Format the response
            response_content = f"**Data**: {response_data['date']}<br>"

            # Format common hours with "am" or "pm"
            formatted_hours = [
                f"{hour}am" if 1 <= hour <= 11 else f"{hour}pm" for hour in response_data["common_hours"]
            ]
            if formatted_hours:
                response_content += "**Horários disponíveis para essa manutenção:**<br>"
                for hour in formatted_hours:
                    response_content += f"- {hour}<br>"
            else:
                response_content += "**Horários disponíveis para essa manutenção**: Nenhum horário disponível<br>"

            # Print found pieces
            if response_data["found_pieces"]:
                response_content += "**Ferramentas disponíveis:**<br>"
                for piece in response_data["found_pieces"]:
                    response_content += f"- {piece['categoria']}: {piece['descricao']} (SAP: {piece['sap']})<br>"
            else:
                response_content += "**Ferramentas disponíveis**: Nenhuma ferramenta encontrada<br>"

            # Print unmatched pieces
            if response_data["unmatched_pieces"]:
                response_content += f"**Ferramentas não encontradas**: {', '.join(response_data['unmatched_pieces'])}<br>"
            else:
                response_content += "**Ferramentas não encontradas**: Todas as ferramentas foram encontradas!<br>"

            # Display the formatted response
            with st.chat_message("assistant"):
                st.markdown(response_content, unsafe_allow_html=True)

            # Save formatted response to session
            st.session_state.messages.append({"role": "assistant", "content": response_content})

        else:
            # Display user-friendly error message if required keys are missing
            error_message = (
                "Desculpe, seja mais claro no prompt. Pergunte sobre a disponibilidade de alguma ferramenta para alguma data ou sobre alguma informação referente ao manual.\n\n"
                "Por exemplo: 'Preciso de uma chave de fenda 5mm e uma máquina de solda e uma serra elétrica para hoje'"
            )
            with st.chat_message("assistant"):
                st.markdown(error_message)

            # Save error message to session
            st.session_state.messages.append({"role": "assistant", "content": error_message})

    else:
        error_message = "Erro ao conectar com o backend."
        with st.chat_message("assistant"):
            st.markdown(error_message)

        # Save error message to session
        st.session_state.messages.append({"role": "assistant", "content": error_message})
