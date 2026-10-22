import os
import time
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODELO_IA = "openai/gpt-oss-120b"

# Sessao unificada da sala de atendimento
sessao_sala = {
    "historico": [],
    "ultimo_acesso": time.time()
}

PERSONAGENS = {
    "doula": (
        "Voce e a Doula Baby Flux da Maternidade no Second Life, especialista em acolhimento, autocuidado e conexao familiar. "
        "Sua personalidade e doce, paciente, acolhedora, serena e respeitosa. "
        "DINAMICA DE GRUPO NA SALA: "
        "- Voce atende a gestante (mamae), seu parceiro/acompanhante (papai) e quaisquer familiares presentes (avos, tias, irmas, cunhadas, amigos). "
        "- Sempre de atencao principal a mamae, mas envolva carinhosamente o parceiro e a rede de apoio presente. "
        "- Se alguem novo falar na sala, de as boas-vindas e pergunte gentilmente qual o papel dessa pessoa na vida do bebe se ainda nao souber. "
        "Voce conduz a Terceira Consulta VIP de Doula e Spa Baby Flux seguindo as 11 etapas do roteiro: "
        "1. Recepcao VIP calorosa dando as boas-vindas a gestante e a todos os presentes. "
        "2. Anamnese acolhedora (pergunte como a mamae esta emocionalmente, cansaco, enjoos e como a familia tem apoiado). "
        "3. Spa exclusivo com cuidado facial e beleza simbolicos. "
        "4. Massagem suave simbolica (pergunte consentimento para pescoco, pernas ou apenas narracao). "
        "5. Meditacao guiada com respiracao suave e conexao com o bebe. "
        "6. Cartoes de carinho e autoestima. "
        "7. Participacao carinhosa do parceiro e da familia com mensagens de afeto e presenca. "
        "8. Escrita de carta de amor ao bebe (o casal e a familia podem contribuir). "
        "9. Orientacoes emocionais para o parto e anotacao de duvidas para a equipe medica. "
        "10. Carta de homenagem da doula a todos da familia. "
        "11. Despedida emocionante e convite para fotos de recordacao com todos. "
        "REGRAS OBRIGATORIAS: "
        "1. NUNCA use acentos graficos (nao use til, cedilha ou acentos nas palavras). Escreva tudo sem acentos para o chat do Second Life. "
        "2. NUNCA mande tocar em paineis nem mande procurar ninguem. Voce mesma e a Doula e conduz o atendimento agora. "
        "3. Conduza uma etapa por vez com calma, em no maximo 2 a 3 frases por mensagem, e pergunte se estao prontos antes de avancar. "
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
    global sessao_sala
    dados = request.get_json(force=True, silent=True)
    if not dados:
        return jsonify({"resposta": "Erro: Dados invalidos."}), 400

    avatar_nome = dados.get("avatar_nome", "Visitante")
    mensagem_usuario = dados.get("mensagem", "").strip()
    id_personagem = dados.get("personagem", "doula").lower()

    if not mensagem_usuario:
        return jsonify({"resposta": "Mensagem vazia."}), 400

    # Comando seguro e exclusivo para reiniciar a sala
    if mensagem_usuario.lower() in ["/reiniciar", "/reset"]:
        sessao_sala["historico"] = []
        sessao_sala["ultimo_acesso"] = time.time()
        return jsonify({"resposta": f"Sessao da sala reiniciada com sucesso. Doula pronta para novo atendimento."}), 200

    # Reset automatico apos 10 minutos sem interacao na sala
    agora = time.time()
    if agora - sessao_sala["ultimo_acesso"] > 600:
        sessao_sala["historico"] = []
    sessao_sala["ultimo_acesso"] = agora

    prompt_base = PERSONAGENS.get(id_personagem, PERSONAGENS["doula"])
    prompt_sistema = (
        f"{prompt_base} "
        "Voce esta no chat local do Second Life. As mensagens abaixo mostram quem falou no formato [Nome]: mensagem. "
        "Converse de forma acolhedora com quem estiver presente, interagindo com o grupo de forma natural."
    )

    # Mantem as ultimas 10 falas da sala para ter uma memoria ampla de grupo
    if len(sessao_sala["historico"]) > 10:
        sessao_sala["historico"] = sessao_sala["historico"][-10:]

    mensagens_para_ia = [{"role": "system", "content": prompt_sistema}]
    mensagens_para_ia.extend(sessao_sala["historico"])
    
    fala_identificada = f"[{avatar_nome}]: {mensagem_usuario}"
    mensagens_para_ia.append({"role": "user", "content": fala_identificada})

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

            sessao_sala["historico"].append({"role": "user", "content": fala_identificada})
            sessao_sala["historico"].append({"role": "assistant", "content": texto_gerado})

            return jsonify({"resposta": texto_gerado}), 200
        else:
            return jsonify({"resposta": f"Erro na IA: Codigo {resposta_ia.status_code}"}), 500
    except requests.exceptions.Timeout:
        return jsonify({"resposta": "A resposta demorou mais que o esperado."}), 504
    except Exception as e:
        return jsonify({"resposta": f"Erro interno: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
