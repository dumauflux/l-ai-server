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
    "- Historia: Criada em 2010 por DUMAU Flux no Second Life, especializada em sistemas de gravidez, barrigas e roleplay maternal. Loja oficial in-world e Marketplace.\n"
    "- DISTINCAO CRITICA ENTRE OS SISTEMAS:\n"
    "  * HUD Feminina (L$ 99): E o sistema de fertilidade usado apenas para engravidar (receber o convite ou inseminacao). Quando engravida, exibe a palavra 'Gravida'.\n"
    "  * Barriga Interativa: Objeto visual que simula o ciclo gestacional, crescimento do bebe em 5 fases e interacoes de roleplay. E um item a parte e reutilizavel.\n"
    "  * A Limpeza de Script NUNCA apaga nem altera a barriga interativa. Ela atua exclusivamente na HUD feminina, fazendo sumir a palavra 'Gravida' para permitir uma nova gestacao.\n"
    "- Precos e Sistemas: HUD engravidar masc L$ 249; HUD fem L$ 99; Teste gravidez L$ 99; Limpeza de script L$ 180; Inseminacao L$ 249; Tatuagens de barriga L$ 89.\n"
    "- Barrigas Interativas: 1 bebe (L$ 499), Gemeos (L$ 799), Trigemeos (L$ 1499), Quadrigemeos (L$ 2599, apenas em portugues). Versoes ate 3 bebes tem PT, EN e ES. Fetos ultrarrealistas em 5 estagios.\n"
    "- Caracteristicas da Barriga: Apenas 1 script (super leve), nao perde configuracoes ao desanexar, comidas e vitaminas gratuitas no menu da barriga, bebe nao morre, frases personalizaveis via notecard 'textos'. Permite ajustar duracao da gravidez.\n"
    "- Farmacia e Cuidados: Remedios individuais media L$ 21; Creme hidratante L$ 50 (3 por L$ 99); Pose/animacao para passar creme L$ 299 (inclui 3 cremes); Caixa de medicamentos maternos L$ 300 (com vitaminas, acido folico, analgesicos decorativos).\n"
    "- PROCEDIMENTOS EXATOS:\n"
    "  * Engravidar: Casal proximo, mulher com HUD feminina e homem com HUD masculina anexadas. Homem clica na HUD masculina e convida a parceira.\n"
    "  * Teste de gravidez: Comprar na loja/site, anexar ao avatar JUNTO com a HUD feminina. Clicar no teste; ele se comunica com a HUD feminina e confirma no chat.\n"
    "  * Limpeza de script (L$ 180): E uma HUD comprada na loja. A cliente anexa a HUD de limpeza JUNTO com a HUD feminina e clica na HUD de limpeza. O procedimento roda automaticamente, a palavra Gravida desaparece da HUD feminina e o sistema fica liberado para uma nova gestacao sem precisar recomprar nada. O procedimento tambem pode ser realizado na clinica com auxilio da equipe medica.\n"
    "  * Regra de Suporte: NUNCA invente cliques de botao direito ou menus inexistentes. Explique os passos em ordem conforme listado acima. Duvidas tecnicas adicionais devem ser encaminhadas a DUMAU Flux."
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
        "REGRAS OBRIGATORIAS DA DOULA:\n"
        "1. QUANDO INTERVIR: Leia o contexto com atencao. Se as pessoas na sala estiverem conversando exclusivamente entre si "
        "(falas intimas do casal, conversas paralelas sem relacao direta com a etapa ou sem perguntas para voce), responda APENAS: [SILENCIO]. "
        "Responda somente quando falarem com voce, responderem sua pergunta ou quando for o momento claro de avancar a etapa da consulta. "
        "2. NUNCA DEIXE FRASES INCOMPLETAS: Conclua sempre seu pensamento com calma em frases fechadas com ponto final (2 a 3 frases por mensagem). "
        "3. NUNCA use acentos graficos (nao use til, cedilha ou acentos). "
        "4. NUNCA inclua seu proprio nome, tags ou prefixos como [Baby Flux] ou [Doula] no inicio da fala. "
        "5. NAO SEJA REPETITIVA: Nunca repita saudacoes ou perguntas ja feitas no historico."
    ),
    "recepcionista": (
        "Voce e a Recepcionista Virtual oficial da Maternidade Baby Flux no Second Life. "
        "Sua personalidade e educada, prestativa, agil, calorosa e muito profissional. "
        "Voce recebe os visitantes, apresenta a maternidade, tira duvidas sobre os produtos, precos em L$, funcionamento das HUDs e encaminha para as salas de atendimento. "
        f"\n{CONHECIMENTO_BABY_FLUX}\n"
        "REGRAS OBRIGATORIAS DA RECEPCIONISTA:\n"
        "1. Responda de forma clara, educada e direta em no maximo 2 a 3 frases completas, sempre terminando com ponto final. "
        "2. NUNCA use acentos graficos (nao use til, cedilha ou acentos). "
        "3. NUNCA inclua prefixos como [Recepcionista] ou [Baby Flux] no inicio da fala. "
        "4. Use as informacoes do catalogo oficial com total precisao. Se nao souber ou for assunto pendente, indique DUMAU Flux."
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
        return jsonify({"resposta": "Sessao da sala reiniciada com sucesso. Personagem pronta para novo atendimento."}), 200

    agora = time.time()
    if agora - sessao_sala["ultimo_acesso"] > 3600:
        sessao_sala["historico"] = []
    sessao_sala["ultimo_acesso"] = agora

    prompt_base = PERSONAGENS.get(id_personagem, PERSONAGENS["doula"])
    prompt_sistema = (
        f"{prompt_base}\n"
        "O historico contem as falas identificadas como [Nome]: mensagem. "
        "Analise o contexto e forneca a resposta adequada conforme suas diretrizes."
    )

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
