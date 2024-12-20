from flask import Flask, request, jsonify
import openai
import psycopg2
import os

app = Flask(__name__)

# Configuração do banco de dados PostgreSQL a partir das variáveis de ambiente
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT')
}

# Configuração da API OpenAI
openai.api_key = os.getenv('API_KEY')

# Conexão com o banco de dados
def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn

def create_table():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Criação da tabela
    cur.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id SERIAL PRIMARY KEY,
            content TEXT NOT NULL
        );
    """)
    
    conn.commit()
    cur.close()
    conn.close()

@app.route('/learn', methods=['POST'])
def learn():
    """
    Adiciona novos dados ao banco de dados.
    """
    data = request.json
    text = data.get('text')
    
    if not text:
        return jsonify({"error": "Texto não fornecido."}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO memories (content) VALUES (%s)", (text,))
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({"message": "Memória armazenada com sucesso."})

@app.route('/recall', methods=['POST'])
def recall():
    """
    Recupera dados baseados em uma consulta em linguagem natural.
    """
    query = request.json.get('query')
    if not query:
        return jsonify({"error": "Consulta não fornecida."}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT content FROM memories")
    memories = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    
    # Processa a consulta usando IA
    context = " ".join(memories)
    prompt = f"Contexto: {context}\n\nPergunta: {query}\nResposta:"
    response = openai.Completion.create(
        engine="gpt-3.5-turbo",
        prompt=prompt,
        max_tokens=150
    )
    
    answer = response.choices[0].text.strip()
    return jsonify({"query": query, "answer": answer})

@app.route('/analyze', methods=['GET'])
def analyze():
    """
    Gera insights baseados nos dados existentes.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT content FROM memories")
    memories = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    
    # Gera insights
    insights_prompt = f"Com base nas seguintes memórias: {', '.join(memories)}, quais são os principais padrões e insights?"
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=insights_prompt,
        max_tokens=200
    )
    
    insights = response.choices[0].text.strip()
    return jsonify({"insights": insights})

if __name__ == "__main__":
    create_table()
    app.run(host='0.0.0.0', port=5000, debug=True)
