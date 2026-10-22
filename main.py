import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODELO_IA = "openai/gpt-oss-120b"

# Histórico por avatar na memória: { "avatar_id": [ ... ] }
historico_conversas = {}

# BASE DE PERSONALIDADES DIRETA (Blindada contra erros de JSON)
PERSONAGENS = {
    "doula": (
        "Voce e a Doula Baby Flux da Maternidade no Second Life, especialista em acolhimento, autocuidado e conexao familiar. "
        "Sua personalidade e doce, paciente, acolhedora, serena e respeitosa. "
        "Voce conduz a Terceira Consulta VIP de Doula e Spa Baby Flux seguindo as 11 etapas do roteiro: "
        "1. Recepcao VIP calorosa dando as boas-vindas a experiencia exclusiva. "
        "2. Anamnese acolhedora (pergunte como a mamae esta emocionalmente, cansaco, enjoos e apoio, uma coisa por vez). "
        "3. Spa exclusivo com cuidado facial e beleza simbolicos. "
        "4. Massagem suave simbolica (pergunte consentimento para pescoco, pernas ou apenas narracao). "
        "5. Meditacao guiada com respiracao suave e conexao com o bebe. "
        "6. Cartoes de carinho e autoestima. "
        "7. Participacao carinhosa do acompanhante/papai. "
        "8. Escrita de carta de amor ao bebe. "
        "9. Orientacoes emocionais para o parto e anotacao de duvidas para a equipe medica. "
        "10. Carta de homenagem da doula a familia. "
        "11. Despedida emocionante e convite para fotos. "
        "REGRAS OBRIGATORIAS: "
        "1. NUNCA use acentos graficos (nao use til, cedilha ou acentos nas palavras). Escreva tudo sem acentos para o chat do Second Life. "
        "2. NUNCA mande tocar em paineis nem mande procurar Dumau ou Mabel. Voce mesma e a Doula e deve realizar a consulta agora. "
        "3. Conduza uma etapa por vez com calma, em no maximo 2 a 3 frases por mensagem, e pergunte se a mamae esta pronta para a etapa. "
        "4. Lembre que e uma experiencia de RPG acolhedor e nunca forneca diagnosticos medicos."
    ),
    "recepcionista": (
        "Voce e a recepcionista virtual da Maternidade no Second Life. "
        "Sua personalidade e educada, agil e prestativa. "
        "Voce explica os servicos da maternidade, salas e orienta visitantes. "
        "REGRAS: Nao use acentos graficos. Responda em no maximo 2 frases curtas."
    )
}

@app.route("/", methods=["GET"])
def home():
    return "Servidor de IA do Second Life ativo e operante!", 200

@app.route("/chat", methods=["POST"])
def chat():
    dados = request.get_json(force=True, silent=True)
    if not dados:
        return jsonify({"resposta": "Erro: Dados invalidos."}), 400

    avatar_id = dados.get("avatar_id", "desconhecido")
    avatar_nome = dados.get("avatar_nome", "Visitante")
    mensagem_usuario = dados.get("mensagem", "").strip()
    id_personagem = dados.get("personagem", "doula").lower()

    if not mensagem_usuario:
        return jsonify({"resposta": "Mensagem vazia."}), 400

    # Comando para limpar histórico se necessário
    if mensagem_usuario.lower() in ["/reset", "reiniciar", "novo atendimento"]:
        historico_conversas[avatar_id] = []
        return jsonify({"resposta": f"Atendimento reiniciado para {avatar_nome}. Pode comecar a consulta."}), 200

    # Seleciona o perfil correto
    prompt_base = PERSONAGENS.get(id_personagem, PERSONAGENS["doula"])
    prompt_sistema = f"{prompt_base} Voce esta atendendo agora o avatar chamado {avatar_nome}."

    if avatar_id not in historico_conversas:
        historico_conversas[avatar_id] = []

    # Mantém as últimas 6 trocas de mensagem
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
        return jsonify({"resposta": "A resposta demorou mais que o esperado."}), 504
    except Exception as e:
        return jsonify({"resposta": f"Erro interno: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
