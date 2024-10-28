import requests
import uuid
import streamlit as st
from dotenv import load_dotenv
import os
import streamlit.components.v1 as components
import base64

# Load environment variables from .env file
load_dotenv()

# Set Tractian blue color
tractian_blue = "#3662e3"

# Custom HTML to set the favicon and title
favicon_path = os.path.join(os.path.dirname(__file__), "images/logo_redonda.txt")
page_title = "TracBOT"  # Title to be displayed on the browser tab


# Function to load base64 from a text file
def load_base64_image(txt_path):
    with open(txt_path, "r") as file:
        return file.read()


# Load base64 images
favicon_base64 = load_base64_image(favicon_path)
logo_base64 = load_base64_image(
    os.path.join(os.path.dirname(__file__), "images/tractian_logo_name.txt")
)


# Set page configuration with base64 favicon
st.set_page_config(
    page_title=page_title, page_icon=f"data:image/png;base64,{favicon_base64}"
)

# Inject custom HTML to set favicon and title in the browser
components.html(
    f"""
    <script>
        document.title = "{page_title}";
        var link = document.createElement("link");
        link.rel = "icon";
        link.href = "data:image/png;base64,{favicon_base64}";
        document.head.appendChild(link);
    </script>
    """,
    height=0,
)

# Display logo using base64
st.image(f"data:image/png;base64,{logo_base64}", width=120)

# Title and app layout
st.title("TracBOT")

# Introduction text
st.markdown(
    f"""
    <p>
    Este é um chatbot que utiliza uma API para responder perguntas sobre a disponibilidade de ferramentas para manutenção e informações referentes ao manual.
    </p>
    <p><strong>Importante: Se você quer fazer alguma pergunta referente ao manual, comece o prompt com "No manual" para garantir uma pesquisa mais precisa!</strong></p>
    """,
    unsafe_allow_html=True,
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
    payload = {"prompt": prompt, "conversation_id": conversation_id}

    # Send request to the backend
    response = requests.post(
        "http://ec2-15-228-54-226.sa-east-1.compute.amazonaws.com:5001/main",
        json=payload,
    )

    if response.status_code == 200:
        # Parse the response JSON
        response_data = response.json()

        # Check if response contains an "answer" key (direct answer format)
        if "answer" in response_data:
            # Display the direct answer in the conversation
            with st.chat_message("assistant"):
                st.markdown(response_data["answer"])

            # Save the direct answer to session
            st.session_state.messages.append(
                {"role": "assistant", "content": response_data["answer"]}
            )

        # Otherwise, check if it contains the structured format
        elif all(
            key in response_data
            for key in ["date", "common_hours", "found_pieces", "unmatched_pieces"]
        ):
            # Format the structured response
            response_content = f"**Data**: {response_data['date']}<br>"

            # Format common hours with "am" or "pm"
            formatted_hours = [
                f"{hour}am" if 1 <= hour <= 11 else f"{hour}pm"
                for hour in response_data["common_hours"]
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
                response_content += (
                    "**Ferramentas disponíveis**: Nenhuma ferramenta encontrada<br>"
                )

            # Print unmatched pieces
            if response_data["unmatched_pieces"]:
                response_content += f"**Ferramentas não encontradas**: {', '.join(response_data['unmatched_pieces'])}<br>"
            else:
                response_content += "**Ferramentas não encontradas**: Todas as ferramentas foram encontradas!<br>"

            # Display the formatted structured response
            with st.chat_message("assistant"):
                st.markdown(response_content, unsafe_allow_html=True)

            # Save formatted structured response to session
            st.session_state.messages.append(
                {"role": "assistant", "content": response_content}
            )

        else:
            # Display user-friendly error message if required keys are missing
            error_message = (
                "Desculpe, seja mais claro no prompt. Pergunte sobre a disponibilidade de alguma ferramenta para alguma data ou sobre alguma informação referente ao manual.\n\n"
                "Por exemplo: 'Preciso de uma chave de fenda 5mm e uma máquina de solda e uma serra elétrica para hoje'"
            )
            with st.chat_message("assistant"):
                st.markdown(error_message)

            # Save error message to session
            st.session_state.messages.append(
                {"role": "assistant", "content": error_message}
            )

    else:
        error_message = "Erro ao conectar com o backend."
        with st.chat_message("assistant"):
            st.markdown(error_message)

        # Save error message to session
        st.session_state.messages.append(
            {"role": "assistant", "content": error_message}
        )
