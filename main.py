import os
import time
import unicodedata
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODELO_IA = "openai/gpt-oss-120b"

sessao_sala = {
    "historico": [],
    "ultimo_acesso": time.time()
}

def remover_acentos(texto):
    """Remove acentos graficos e caracteres especiais para o Second Life"""
    nfkd = unicodedata.normalize('NFKD', texto)
    return "".join([c for c in nfkd if not unicodedata.combining(c)])

CONHECIMENTO_BABY_FLUX = (
    "CONHECIMENTO INSTITUCIONAL E CATALOGO BABY FLUX:\n"
    "- Historia: Criada em 2010 por DUMAU Flux no Second Life, especializada em sistemas de gravidez, barrigas e roleplay maternal. Loja oficial in-world e no Marketplace.\n"
    "- Precos e Sistemas: HUD engravidar masc L$ 249; HUD fem L$ 99; Teste gravidez L$ 99; Limpeza de script L$ 180; Inseminacao L$ 249; Tatuagens de barriga L$ 89.\n"
    "- Barrigas Interativas: 1 bebe (L$ 499), Gemeos (L$ 799), Trigemeos (L$ 1499), Quadrigemeos (L$ 2599, apenas portugues). Versoes ate 3 bebes tem PT, EN e ES. Fetos ultrarrealistas em 5 estagios.\n"
    "- Caracteristicas da Barriga: Apenas 1 script (super leve), nao perde configuracoes ao desanexar, comidas e vitaminas gratuitas no menu, bebe nao morre, frases personalizaveis via notecard 'textos'. Permite ajustar duracao da gravidez.\n"
    "- Farmacia e Cuidados: Remedios individuais media L$ 21; Creme hidratante L$ 50 (3 por L$ 99); Pose/animacao para passar creme L$ 299 (inclui 3 cremes); Caixa de medicamentos maternos L$ 300 (com vitaminas, acido folico, analgesicos decorativos).\n"
    "- Procedimentos: Para engravidar, ambos com HUDs proximos; Teste precisa da HUD feminina anexada; Limpeza de script prepara para novo ciclo e evita recompra de barriga/HUD; Se tiver duvida nao listada, oriente a falar com a equipe ou DUMAU Flux.\n"
)

PERSONAGENS = {
    "doula": (
        "Voce e a Doula da Maternidade Baby Flux no Second Life, especialista em acolhimento, autocuidado e conexao familiar. "
        "Sua personalidade e doce, paciente, acolhedora, serena, discreta e respeitosa. "
        "Voce atende a gestante (mamae), seu parceiro/acompanhante (papai) e familiares presentes. "
        "Voce conduz a Terceira Consulta VIP de Doula e Spa Baby Flux seguindo as 11 etapas do roteiro: "
        "1. Recepcao VIP calorosa dando as boas-vindas. "
        "2. Anamnese acolhedora (pergunte como a mamae esta emocionalmente, cansaco, enjoos e apoio, uma pergunta por vez). "
        "3. Spa exclusivo com cuidado facial e beleza simbolicos. "
        "4. Massagem suave simbolica (pergunte consentimento para pescoco, pernas ou apenas narracao). "
        "5. Meditacao guiada com respiracao suave e conexao com o bebe. "
        "6. Cartoes de carinho e autoestima. "
        "7. Participacao carinhosa do parceiro e da familia. "
        "8. Escrita de carta de amor ao bebe. "
        "9. Orientacoes emocionais para o parto e anotacao de duvidas para a equipe medica. "
        "10. Carta de homenagem da doula a familia. "
        "11. Despedida emocionante e convite para fotos de recordacao. "
        f"\n{CONHECIMENTO_BABY_FLUX}\n"
        "REGRAS OBRIGATORIAS:\n"
        "1. QUANDO INTERVIR: Leia o contexto com atencao. Se as pessoas na sala estiverem conversando exclusivamente entre si "
        "(falas intimas do casal, conversas paralelas sem relacao direta com a etapa ou sem perguntas para voce), responda APENAS: [SILENCIO]. "
        "Responda somente quando falarem com voce, responderem sua pergunta ou quando for o momento claro de avancar a etapa da consulta. "
        "2. NUNCA DEIXE FRASES INCOMPLETAS: Sempre conclua seu pensamento com clareza. Use de 2 a 3 frases completas, terminando sempre com ponto final. "
        "3. NUNCA use acentos graficos (nao use til, cedilha ou acentos). "
        "4. NUNCA inclua seu proprio nome, tags ou prefixos como [Baby Flux] ou [Doula] no inicio da fala. "
        "5. NAO SEJA REPETITIVA: Nunca repita a mesma frase de abertura ou pergunta que ja fez nas falas anteriores. Avance a conversa com naturalidade."
    ),
    "recepcionista": (
        "Voce e a recepcionista virtual da Maternidade Baby Flux no Second Life. "
        "Sua personalidade e educada, prestativa e agil. "
        f"{CONHECIMENTO_BABY_FLUX} "
        "REGRAS: Nao use acentos graficos. Responda em no maximo 2 frases curtas e objetivas."
    )
}

@app.route("/", methods=["GET"])
def home():
    return "Servidor de IA Baby Flux operante!", 200

@app.route("/chat", methods=["POST"])
def chat():
    global sessao_sala
    dados = request.get_json(force=True, silent=True)
    if not dados:
        return jsonify({"resposta": ""}), 400

    avatar_nome = dados.get("avatar_nome", "Visitante")
    mensagem_usuario = dados.get("mensagem", "").strip()
    id_personagem = dados.get("personagem", "doula").lower()

    if not mensagem_usuario:
        return jsonify({"resposta": ""}), 400

    if mensagem_usuario.lower() in ["/reiniciar", "/reset"]:
        sessao_sala["historico"] = []
        sessao_sala["ultimo_acesso"] = time.time()
        return jsonify({"resposta": "Sessao da sala reiniciada com sucesso. Doula pronta para novo atendimento."}), 200

    # Memoria estendida: expira apos 1 hora de inatividade
    agora = time.time()
    if agora - sessao_sala["ultimo_acesso"] > 3600:
        sessao_sala["historico"] = []
    sessao_sala["ultimo_acesso"] = agora

    prompt_base = PERSONAGENS.get(id_personagem, PERSONAGENS["doula"])
    prompt_sistema = (
        f"{prompt_base}\n"
        "O historico contem as falas identificadas como [Nome]: mensagem. "
        "Analise se a ultima fala requer intervencao profissional ou se deve responder [SILENCIO]."
    )

    # Guarda ate 30 interacoes da consulta
    if len(sessao_sala["historico"]) > 30:
        sessao_sala["historico"] = sessao_sala["historico"][-30:]

    mensagens_para_ia = [{"role": "system", "content": prompt_sistema}]
    mensagens_para_ia.extend(sessao_sala["historico"])
    
    fala_identificada = f"[{avatar_nome}]: {mensagem_usuario}"
    mensagens_para_ia.append({"role": "user", "content": fala_identificada})

    payload = {
        "model": MODELO_IA,
        "max_tokens": 450,
        "temperature": 0.65,
        "messages": mensagens_para_ia
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        resposta_ia = requests.post(GROQ_URL, json=payload, headers=headers, timeout=20)
        if resposta_ia.status_code == 200:
            resultado_json = resposta_ia.json()
            texto_gerado = resultado_json["choices"][0]["message"]["content"].strip()
            
            if "[silencio]" in texto_gerado.lower():
                sessao_sala["historico"].append({"role": "user", "content": fala_identificada})
                return jsonify({"resposta": ""}), 200

            texto_limpo = remover_acentos(texto_gerado)

            sessao_sala["historico"].append({"role": "user", "content": fala_identificada})
            sessao_sala["historico"].append({"role": "assistant", "content": texto_limpo})

            return jsonify({"resposta": texto_limpo}), 200
        else:
            return jsonify({"resposta": ""}), 500
    except requests.exceptions.Timeout:
        return jsonify({"resposta": ""}), 504
    except Exception as e:
        return jsonify({"resposta": ""}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
