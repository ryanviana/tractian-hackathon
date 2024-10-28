import os
import json
from flask import Flask, request, jsonify
import psycopg2
import openai
from dotenv import load_dotenv
from datetime import date

load_dotenv()

app = Flask(__name__)

# Configurar a API do OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Configurar a conexão com o banco de dados
def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    return conn

# Rota principal
@app.route('/consulta', methods=['POST'])
def consulta():
    data = request.get_json()
    prompt = data.get('prompt', '')
    if not prompt:
        return jsonify({'error': 'Prompt não fornecido.'}), 400

    try:
        # Passo 1: Extrair as peças do prompt
        piece_descriptions = extract_pieces(prompt)

        if not piece_descriptions:
            return jsonify({'message': 'Nenhuma peça identificada no prompt.'}), 200

        # Passo 2: Obter informações das peças
        pieces_info = get_pieces_info(piece_descriptions)

        if not pieces_info:
            return jsonify({'message': 'Nenhuma peça encontrada com as descrições fornecidas.'}), 200

        # Obter os códigos SAP
        saps = [piece['sap'] for piece in pieces_info]

        # Passo 3: Consultar a disponibilidade
        common_hours = get_common_availability(saps)

        # Passo 4: Retornar os resultados
        response = {
            'pieces': pieces_info,
            'common_hours': common_hours
        }
        return jsonify(response), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Erro ao processar a consulta.'}), 500

def extract_pieces(prompt):
    messages = [
        {
            'role': 'system',
            'content': 'Você é um assistente que extrai nomes de peças mencionadas em um texto. Retorne apenas uma lista de peças em formato JSON. Exemplo: ["peça1", "peça2"]'
        },
        {'role': 'user', 'content': prompt}
    ]

    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=messages,
        temperature=0
    )

    assistant_message = response['choices'][0]['message']['content']

    try:
        pieces_list = json.loads(assistant_message)
        return pieces_list
    except json.JSONDecodeError:
        return []

def get_pieces_info(descriptions):
    conn = get_db_connection()
    cur = conn.cursor()

    # Construir a consulta SQL dinâmica
    placeholders = ', '.join(['%s'] * len(descriptions))
    sql = f"""
        SELECT sap, categoria, descricao
        FROM pieces
        WHERE {" OR ".join(["descricao ILIKE %s" for _ in descriptions])}
    """
    values = [f"%{desc}%" for desc in descriptions]

    cur.execute(sql, values)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    pieces = []
    for row in rows:
        pieces.append({
            'sap': row[0],
            'categoria': row[1],
            'descricao': row[2]
        })

    return pieces

def get_common_availability(saps):
    conn = get_db_connection()
    cur = conn.cursor()

    placeholders = ', '.join(['%s'] * len(saps))
    sql = f"""
        SELECT hora
        FROM availability
        WHERE sap IN ({placeholders}) AND data = %s AND ocupado = FALSE
        GROUP BY hora
        HAVING COUNT(DISTINCT sap) = %s
        ORDER BY hora;
    """
    values = saps + [date.today(), len(saps)]

    cur.execute(sql, values)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    hours = [row[0] for row in rows]

    return hours

if __name__ == '__main__':
    app.run(debug=True)
