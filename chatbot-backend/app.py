import os
import json
import re
from flask import Flask, request, jsonify
import psycopg2
from openai import OpenAI
from dotenv import load_dotenv
from datetime import date

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


@app.route("/consulta", methods=["POST"])
def consulta():
    data = request.get_json()
    prompt = data.get("prompt", "")
    if not prompt:
        return jsonify({"error": "Prompt não fornecido."}), 400

    try:
        print("Starting piece extraction...")
        piece_descriptions = extract_pieces(prompt)
        print("Piece descriptions:", piece_descriptions)

        if not piece_descriptions:
            return jsonify({"message": "Nenhuma peça identificada no prompt."}), 200

        print("Getting piece info...")
        pieces_info = get_pieces_info(piece_descriptions)
        print("Pieces info:", pieces_info)

        if not pieces_info:
            return (
                jsonify(
                    {
                        "message": "Nenhuma peça encontrada com as descrições fornecidas.",
                        "extracted_pieces": piece_descriptions,
                    }
                ),
                200,
            )

        saps = [piece["sap"] for piece in pieces_info]

        print("Checking availability...")
        common_hours = get_common_availability(saps)
        print("Common hours:", common_hours)

        response = {"pieces": pieces_info, "common_hours": common_hours}
        return jsonify(response), 200

    except Exception as e:
        print("Detailed error in /consulta route:", e)
        import traceback

        traceback.print_exc()
        return jsonify({"error": f"Erro ao processar a consulta: {str(e)}"}), 500


def extract_pieces(prompt):
    try:
        messages = [
            {
                "role": "system",
                "content": (
                    "Você é um assistente que extrai nomes de peças mencionadas em um texto. "
                    "Retorne apenas uma lista de peças em formato JSON válido, sem texto adicional. "
                    'Exemplo: ["peça1", "peça2"]'
                ),
            },
            {"role": "user", "content": prompt},
        ]

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use the model you have access to
            messages=messages,
            temperature=0,
        )

        assistant_message = response.choices[0].message.content
        print("Assistant's raw response:", assistant_message)

        # Extract JSON array from the assistant's response
        match = re.search(r"\[.*\]", assistant_message, re.DOTALL)
        if match:
            json_array_str = match.group(0)
            print("Extracted JSON array string:", json_array_str)
            pieces_list = json.loads(json_array_str)
            print("Parsed pieces list:", pieces_list)
            return pieces_list
        else:
            print("No JSON array found in the assistant's response.")
            return []

    except json.JSONDecodeError as e:
        print("JSONDecodeError:", e)
        print("Assistant's response caused JSONDecodeError:", assistant_message)
        return []

    except Exception as e:
        print("Error in extract_pieces:", e)
        import traceback

        traceback.print_exc()
        return []


def get_pieces_info(descriptions):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Set similarity threshold if desired
        # cur.execute("SELECT set_limit(0.4);")  # Optional: set the similarity threshold globally

        pieces = []

        for desc in descriptions:
            normalized_desc = desc.upper()
            sql = """
                SELECT sap, categoria, descricao,
                       similarity(unaccent(UPPER(descricao)), unaccent(%s)) AS sim_score
                FROM pieces
                WHERE similarity(unaccent(UPPER(descricao)), unaccent(%s)) >= 0.4
                ORDER BY sim_score DESC
                LIMIT 1;
            """
            cur.execute(sql, (normalized_desc, normalized_desc))
            row = cur.fetchone()
            if row:
                pieces.append({"sap": row[0], "categoria": row[1], "descricao": row[2]})
            else:
                print(f"No match found for '{desc}'")

        cur.close()
        conn.close()

        return pieces

    except Exception as e:
        print("Error in get_pieces_info:", e)
        import traceback

        traceback.print_exc()
        return []


def get_common_availability(saps):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        placeholders = ", ".join(["%s"] * len(saps))
        sql = f"""
            SELECT hora
            FROM availability
            WHERE sap IN ({placeholders}) AND data = %s AND ocupado = FALSE
            GROUP BY hora
            HAVING COUNT(DISTINCT sap) = %s
            ORDER BY hora;
        """
        values = saps + [date.today(), len(saps)]
        print("SQL Query:", cur.mogrify(sql, values))

        cur.execute(sql, values)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        hours = [row[0] for row in rows]
        return hours

    except Exception as e:
        print("Error in get_common_availability:", e)
        return []


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5001)), debug=True)
