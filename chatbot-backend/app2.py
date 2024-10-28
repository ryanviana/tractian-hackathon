import os
import json
import re
from flask import Flask, request, jsonify
import psycopg2
from openai import OpenAI
from dotenv import load_dotenv
from datetime import date, datetime, timedelta
from collections import defaultdict
import dateparser
import numpy as np
import faiss
import PyPDF2
import traceback

load_dotenv()

app = Flask(__name__)

# Configure OpenAI API client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Conversation store to maintain conversation history
conversation_store = defaultdict(list)


# Database connection setup
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


def consulta(prompt, conversation_id):
    try:
        conversation_history = conversation_store[conversation_id]

        piece_descriptions, date_str, conversation_history = extract_pieces(
            prompt, conversation_history
        )

        conversation_store[conversation_id] = conversation_history

        if not piece_descriptions and not date_str:
            return (
                jsonify({"message": "Nenhuma peça ou data identificada no prompt."}),
                200,
            )

        if not piece_descriptions:
            for message in reversed(conversation_history):
                if message["role"] == "assistant":
                    match = re.search(r"\{.*\}", message["content"], re.DOTALL)
                    if match:
                        json_obj_str = re.sub(r"\s+", " ", match.group(0))
                        data = json.loads(json_obj_str)
                        piece_descriptions = data.get("pieces", [])
                        break

        pieces_info, matched_descriptions = get_pieces_info(piece_descriptions)
        unmatched_pieces = list(set(piece_descriptions) - set(matched_descriptions))

        saps = [piece["sap"] for piece in pieces_info]

        # Parse the date string into a datetime.date object, defaulting to today if none provided
        if date_str:
            parsed_date = dateparser.parse(
                date_str, settings={"PREFER_DATES_FROM": "future"}
            )
            if parsed_date:
                parsed_date = parsed_date.date()
            else:
                parsed_date = date.today()
        else:
            parsed_date = date.today()

        common_hours = get_common_availability(saps, target_date=parsed_date)

        response = {
            "found_pieces": pieces_info,
            "unmatched_pieces": unmatched_pieces,
            "common_hours": common_hours,
            "date": parsed_date.isoformat(),
        }
        return jsonify(response), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Erro ao processar a consulta: {str(e)}"}), 500


def consulta_manual(prompt, conversation_id):
    try:
        conversation_history = conversation_store[conversation_id]

        answer = answer_question(prompt, index, embeddings)

        # Save the prompt and answer to conversation history
        conversation_store[conversation_id].append({"role": "user", "content": prompt})
        conversation_store[conversation_id].append(
            {"role": "assistant", "content": answer}
        )

        return jsonify({"answer": answer}), 200

    except Exception as e:
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
                    "Retorne apenas um JSON válido com as peças e a data em formato ISO (AAAA-MM-DD), resolvendo datas relativas como 'hoje' ou 'amanhã' para datas absolutas, sem texto adicional. "
                    'Exemplo: {"pieces": ["peça1", "peça2"], "date": "2024-10-29"}'
                ),
            },
            *conversation_history,
            {"role": "user", "content": prompt},
        ]

        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages,
            temperature=0,
        )

        assistant_message = response.choices[0].message.content

        conversation_history.append({"role": "user", "content": prompt})
        conversation_history.append({"role": "assistant", "content": assistant_message})

        match = re.search(r"\{.*\}", assistant_message, re.DOTALL)
        if match:
            json_obj_str = re.sub(r"\s+", " ", match.group(0))
            data = json.loads(json_obj_str)
            pieces_list = data.get("pieces", [])
            date_str = data.get("date", None)
            return pieces_list, date_str, conversation_history
        else:
            return [], None, conversation_history

    except Exception as e:
        traceback.print_exc()
        return [], None, conversation_history


def get_pieces_info(descriptions):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        similarity_threshold = 0.75

        pieces, matched_descriptions = [], []

        for desc in descriptions:
            sql = """
                SELECT sap, categoria, descricao,
                       similarity(unaccent(UPPER(descricao)), unaccent(%s)) AS sim_score
                FROM pieces
                WHERE similarity(unaccent(UPPER(descricao)), unaccent(%s)) >= %s
                ORDER BY sim_score DESC
                LIMIT 1;
            """
            cur.execute(sql, (desc.upper(), desc.upper(), similarity_threshold))
            row = cur.fetchone()
            if row:
                pieces.append({"sap": row[0], "categoria": row[1], "descricao": row[2]})
                matched_descriptions.append(desc)

        cur.close()
        conn.close()
        return pieces, matched_descriptions

    except Exception as e:
        traceback.print_exc()
        return [], []


def get_common_availability(saps, target_date=None):
    try:
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

        cur.execute(sql, values)
        hours = [row[0] for row in cur.fetchall()]

        cur.close()
        conn.close()
        return hours

    except Exception as e:
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
        model="gpt-4-turbo", messages=messages, temperature=0
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
