import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODELO_IA = "openai/gpt-oss-120b"

# Guarda histórico: { "avatar_id": [ {"role": "...", "content": "..."} ] }
historico_conversas = {}

def carregar_personagens():
    try:
        with open("personagens.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar personagens: {e}")
        return {}

@app.route("/", methods=["GET"])
def home():
    return "Servidor de IA do Second Life ativo e operante!", 200

@app.route("/chat", methods=["POST"])
def chat():
    dados = request.get_json(force=True, silent=True)
    if not dados:
        return jsonify({"resposta": "Erro: Dados invalidos enviados ao servidor."}), 400

    avatar_id = dados.get("avatar_id", "desconhecido")
    avatar_nome = dados.get("avatar_nome", "Visitante")
    mensagem_usuario = dados.get("mensagem", "").strip()
    id_personagem = dados.get("personagem", "doula").lower()

    if not mensagem_usuario:
        return jsonify({"resposta": "Nenhuma mensagem recebida."}), 400

    # Comando para resetar a memória do visitante se desejar começar do zero
    if mensagem_usuario.lower() in ["/reset", "reiniciar", "novo atendimento"]:
        historico_conversas[avatar_id] = []
        return jsonify({"resposta": f"Atendimento reiniciado com sucesso para {avatar_nome}."}), 200

    personagens = carregar_personagens()
    perfil = personagens.get(id_personagem, personagens.get("doula", {}))

    prompt_sistema = (
        f"{perfil.get('personalidade', '')} "
        f"{perfil.get('conhecimentos', '')} "
        f"{perfil.get('regras', '')} "
        f"Voce esta falando com {avatar_nome}. Conduza a consulta ativamente, com carinho, fazendo as perguntas da etapa atual."
    )

    if avatar_id not in historico_conversas:
        historico_conversas[avatar_id] = []

    # Mantém as últimas 6 mensagens de histórico
    if len(historico_conversas[avatar_id]) > 6:
        historico_conversas[avatar_id] = historico_conversas[avatar_id][-6:]

    mensagens_para_ia = [{"role": "system", "content": prompt_sistema}]
    mensagens_para_ia.extend(historico_conversas[avatar_id])
    mensagens_para_ia.append({"role": "user", "content": mensagem_usuario})

    payload = {
        "model": MODELO_IA,
        "max_tokens": 300,
        "temperature": 0.7,
        "messages": mensagens_para_ia
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        resposta_ia = requests.post(GROQ_URL, json=payload, headers=headers, timeout=15)
        if resposta_ia.status_code == 200:
            resultado_json = resposta_ia.json()
            texto_gerado = resultado_json["choices"][0]["message"]["content"].strip()

            historico_conversas[avatar_id].append({"role": "user", "content": mensagem_usuario})
            historico_conversas[avatar_id].append({"role": "assistant", "content": texto_gerado})

            return jsonify({"resposta": texto_gerado}), 200
        else:
            return jsonify({"resposta": f"Erro na IA: Codigo {resposta_ia.status_code}"}), 500
    except requests.exceptions.Timeout:
        return jsonify({"resposta": "Desculpe, a resposta demorou mais que o esperado."}), 504
    except Exception as e:
        return jsonify({"resposta": f"Erro interno: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
