import os
import json
import re
from flask import Flask, request, jsonify
import psycopg2
from openai import OpenAI
from dotenv import load_dotenv
from datetime import date
from collections import defaultdict
import dateparser
import numpy as np
import faiss
import PyPDF2

load_dotenv()

# Print environment variables to verify .env is working
print("OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))
print("DB_HOST:", os.getenv("DB_HOST"))
print("DB_PORT:", os.getenv("DB_PORT"))
print("DB_NAME:", os.getenv("DB_NAME"))
print("DB_USER:", os.getenv("DB_USER"))
print("DB_PASSWORD:", os.getenv("DB_PASSWORD"))

app = Flask(__name__)

# Configure OpenAI API client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)

# Conversation store to maintain conversation history
conversation_store = defaultdict(list)


# Database connection
def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
    return conn


@app.route("/main", methods=["POST"])
def consulta_or_manual():
    data = request.get_json()
    prompt = data.get("prompt", "")
    conversation_id = data.get("conversation_id", None)
    if not prompt:
        return jsonify({"error": "Prompt não fornecido."}), 400
    if not conversation_id:
        return jsonify({"error": "conversation_id não fornecido."}), 400

    # Determine if the request is a manual-related query or a parts-related query
    if is_manual_query(prompt):
        return consulta_manual(prompt, conversation_id)
    else:
        return consulta(prompt, conversation_id)


def is_manual_query(prompt):
    # Basic keyword check to see if the prompt is related to the manual
    manual_keywords = ["manual", "guide", "instruction"]
    return any(keyword in prompt.lower() for keyword in manual_keywords)


def consulta_manual(prompt, conversation_id):
    try:

        answer = answer_question(prompt, index, embeddings)

        # Save the prompt and answer to conversation history
        conversation_store[conversation_id].append({"role": "user", "content": prompt})
        conversation_store[conversation_id].append(
            {"role": "assistant", "content": answer}
        )

        return jsonify({"answer": answer}), 200

    except Exception as e:
        print("Detailed error in /main route:", e)
        import traceback

        traceback.print_exc()
        return jsonify({"error": f"Erro ao processar a consulta: {str(e)}"}), 500


@app.route("/consulta", methods=["POST"])
def consulta(prompt, conversation_id):
    data = request.get_json()
    prompt = data.get("prompt", "")
    conversation_id = data.get("conversation_id", None)
    if not prompt:
        return jsonify({"error": "Prompt não fornecido."}), 400

    if not conversation_id:
        return jsonify({"error": "conversation_id não fornecido."}), 400

    try:
        # Retrieve the conversation history
        conversation_history = conversation_store[conversation_id]

        print("Starting piece extraction...")
        piece_descriptions, date_str, conversation_history = extract_pieces(
            prompt, conversation_history
        )
        print("Piece descriptions:", piece_descriptions)
        print("Extracted date string:", date_str)

        # Update the conversation store
        conversation_store[conversation_id] = conversation_history

        if not piece_descriptions and not date_str:
            return (
                jsonify({"message": "Nenhuma peça ou data identificada no prompt."}),
                200,
            )

        print("Getting piece info...")
        if not piece_descriptions:
            # If no new pieces are mentioned, use the last known pieces
            # Retrieve from conversation history
            for message in reversed(conversation_history):
                if message["role"] == "assistant":
                    match = re.search(r"\{.*\}", message["content"], re.DOTALL)
                    if match:
                        json_obj_str = match.group(0)
                        json_obj_str = re.sub(r"\s+", " ", json_obj_str)
                        data = json.loads(json_obj_str)
                        piece_descriptions = data.get("pieces", [])
                        break
            print("Using previous piece descriptions:", piece_descriptions)

        pieces_info, matched_descriptions = get_pieces_info(piece_descriptions)
        print("Pieces info:", pieces_info)

        # Find pieces not found in the database
        unmatched_pieces = list(set(piece_descriptions) - set(matched_descriptions))
        print("Unmatched pieces:", unmatched_pieces)

        saps = [piece["sap"] for piece in pieces_info]

        print("Checking availability...")
        # Parse the date string into a datetime.date object
        if date_str:
            parsed_date = dateparser.parse(date_str).date()
        else:
            parsed_date = date.today()

        common_hours = get_common_availability(saps, target_date=parsed_date)
        print("Common hours:", common_hours)

        response = {
            "found_pieces": pieces_info,
            "unmatched_pieces": unmatched_pieces,
            "common_hours": common_hours,
            "date": parsed_date.isoformat(),
        }
        return jsonify(response), 200

    except Exception as e:
        print("Detailed error in /consulta route:", e)
        import traceback

        traceback.print_exc()
        return jsonify({"error": f"Erro ao processar a consulta: {str(e)}"}), 500


def extract_pieces(prompt, conversation_history):
    try:
        messages = [
            {
                "role": "system",
                "content": (
                    "Você é um assistente que ajuda a identificar peças e datas mencionadas em um texto. "
                    "Mantenha o contexto da conversa ao interpretar o pedido do usuário. "
                    "Retorne apenas um JSON válido com as peças e a data, sem texto adicional. "
                    'Exemplo: {"pieces": ["peça1", "peça2"], "date": "2024-10-29"}'
                ),
            },
            # Include previous messages
            *conversation_history,
            {"role": "user", "content": prompt},
        ]

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use the model you have access to
            messages=messages,
            temperature=0,
        )

        assistant_message = response.choices[0].message.content
        print("Assistant's raw response:", assistant_message)

        # Update conversation history with assistant's response
        conversation_history.append({"role": "user", "content": prompt})
        conversation_history.append({"role": "assistant", "content": assistant_message})

        # Extract JSON object from the assistant's response
        match = re.search(r"\{.*\}", assistant_message, re.DOTALL)
        if match:
            json_obj_str = match.group(0)
            print("Extracted JSON object string:", json_obj_str)
            # Remove any whitespace and line breaks to ensure valid JSON
            json_obj_str = re.sub(r"\s+", " ", json_obj_str)
            data = json.loads(json_obj_str)
            print("Parsed data:", data)
            pieces_list = data.get("pieces", [])
            date_str = data.get("date", None)
            return pieces_list, date_str, conversation_history
        else:
            print("No JSON object found in the assistant's response.")
            return [], None, conversation_history

    except json.JSONDecodeError as e:
        print("JSONDecodeError:", e)
        print("Assistant's response caused JSONDecodeError:", assistant_message)
        return [], None, conversation_history

    except Exception as e:
        print("Error in extract_pieces:", e)
        import traceback

        traceback.print_exc()
        return [], None, conversation_history


def get_pieces_info(descriptions):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Set similarity threshold
        similarity_threshold = 0.75

        pieces = []
        matched_descriptions = []

        for desc in descriptions:
            normalized_desc = desc.upper()
            sql = """
                SELECT sap, categoria, descricao,
                       similarity(unaccent(UPPER(descricao)), unaccent(%s)) AS sim_score
                FROM pieces
                WHERE similarity(unaccent(UPPER(descricao)), unaccent(%s)) >= %s
                ORDER BY sim_score DESC
                LIMIT 1;
            """
            cur.execute(sql, (normalized_desc, normalized_desc, similarity_threshold))
            row = cur.fetchone()
            if row:
                pieces.append({"sap": row[0], "categoria": row[1], "descricao": row[2]})
                matched_descriptions.append(desc)
            else:
                print(f"No match found for '{desc}'")

        cur.close()
        conn.close()

        return pieces, matched_descriptions

    except Exception as e:
        print("Error in get_pieces_info:", e)
        import traceback

        traceback.print_exc()
        return [], []


def get_common_availability(saps, target_date=None):
    try:
        if not saps:
            print("No SAPs provided for availability check.")
            return []

        conn = get_db_connection()
        cur = conn.cursor()

        if target_date is None:
            target_date = date.today()

        placeholders = ", ".join(["%s"] * len(saps))
        sql = f"""
            SELECT hora
            FROM availability
            WHERE sap IN ({placeholders}) AND data = %s AND ocupado = FALSE
            GROUP BY hora
            HAVING COUNT(DISTINCT sap) = %s
            ORDER BY hora;
        """
        values = saps + [target_date, len(saps)]
        print("SQL Query:", cur.mogrify(sql, values))

        cur.execute(sql, values)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        hours = [row[0] for row in rows]
        return hours

    except Exception as e:
        print("Error in get_common_availability:", e)
        import traceback

        traceback.print_exc()
        return []


def extract_text_from_pdf(pdf_path):
    chunks = []
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                chunks.append({"text": text, "page": page_num + 1})
    return chunks


def create_embeddings(chunks):
    embeddings = []
    for chunk in chunks:
        response = client.embeddings.create(
            input=chunk["text"], model="text-embedding-ada-002"
        )
        embedding = response.data[0].embedding
        embeddings.append(
            {"embedding": embedding, "text": chunk["text"], "page": chunk["page"]}
        )
    return embeddings


def store_embeddings(embeddings):
    dimension = len(embeddings[0]["embedding"])
    index = faiss.IndexFlatL2(dimension)
    vectors = np.array([e["embedding"] for e in embeddings]).astype("float32")
    index.add(vectors)
    return index


def answer_question(question, index, embeddings, k=3):
    response = client.embeddings.create(input=question, model="text-embedding-ada-002")
    question_embedding = np.array(response.data[0].embedding).astype("float32")

    distances, indices = index.search(np.array([question_embedding]), k)
    relevant_chunks = [embeddings[i] for i in indices[0]]

    context = "\n\n".join(
        [f"Página {chunk['page']}: {chunk['text']}" for chunk in relevant_chunks]
    )

    messages = [
        {
            "role": "system",
            "content": "Você é um assistente que responde perguntas com base no seguinte manual.",
        },
        {"role": "system", "content": context},
        {"role": "user", "content": question},
    ]

    response = client.chat.completions.create(
        model="gpt-4", messages=messages, temperature=0
    )

    answer = response.choices[0].message.content.strip()
    pages = [str(chunk["page"]) for chunk in relevant_chunks]
    answer += f"\n\nReferências: Páginas {', '.join(pages)} do manual."
    return answer


# Load and process the manual PDF
pdf_path = "manual.pdf"
chunks = extract_text_from_pdf(pdf_path)
embeddings = create_embeddings(chunks)
index = store_embeddings(embeddings)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5001)), debug=True)
