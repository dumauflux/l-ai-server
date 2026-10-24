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
    "- Historia e Fundadores: Criada em 2010 por DUMAU Flux no Second Life, especializada em sistemas de gravidez, barrigas e roleplay maternal. "
    "DUMAU Flux e casado com Mabel Flux (drapatylove) desde 11/07/2025, sendo casados tanto no Second Life quanto na vida real (RL). Eles sao os proprietarios da Baby Flux. "
    "Possui loja oficial in-world e no Marketplace.\n"
    "- DISTINCAO CRITICA ENTRE OS SISTEMAS:\n"
    "  * HUD Feminina (L$ 99): Sistema de fertilidade usado apenas para engravidar. Quando engravida, exibe a palavra 'Gravida'.\n"
    "  * Barriga Interativa: Objeto visual que simula o ciclo gestacional, crescimento do bebe em 5 fases e interacoes. E reutilizavel.\n"
    "  * A Limpeza de Script NUNCA apaga nem altera a barriga interativa. Ela atua exclusivamente na HUD feminina, fazendo sumir a palavra 'Gravida' para permitir uma nova gestacao.\n"
    "- Precos e Sistemas: HUD engravidar masc L$ 249; HUD fem L$ 99; Teste gravidez L$ 99; Limpeza de script L$ 180; Inseminacao L$ 249; Tatuagens de barriga L$ 89.\n"
    "- Barrigas Interativas: 1 bebe (L$ 499), Gemeos (L$ 799), Trigemeos (L$ 1499), Quadrigemeos (L$ 2599, apenas em portugues). Versoes ate 3 bebes tem PT, EN e ES. Fetos ultrarrealistas em 5 estagios.\n"
    "- Caracteristicas da Barriga: Apenas 1 script (super leve), nao perde configuracoes ao desanexar, comidas e vitaminas gratuitas no menu da barriga, bebe nao morre, frases personalizaveis via notecard 'textos'. Permite ajustar duracao da gravidez.\n"
    "- Farmacia e Cuidados: Remedios individuais media L$ 21; Creme hidratante L$ 50 (3 por L$ 99); Pose/animacao para passar creme L$ 299 (inclui 3 cremes); Caixa de medicamentos maternos L$ 300 (com vitaminas, acido folico, analgesicos decorativos).\n"
    "- PROCEDIMENTOS EXATOS:\n"
    "  * Engravidar: Casal proximo, mulher com HUD feminina e homem com HUD masculina anexadas. Homem clica na HUD masculina e convida a parceira.\n"
    "  * Teste de gravidez: Comprar na loja/site, anexar ao avatar JUNTO com a HUD feminina. Clicar no teste; ele se comunica com a HUD feminina e confirma no chat.\n"
    "  * Limpeza de script (L$ 180): E uma HUD comprada na loja. A cliente anexa a HUD de limpeza JUNTO com a HUD feminina e clica nela. Procedimento automatico, palavra Gravida desaparece da HUD feminina. Tambem pode ser feito na clinica com auxilio da equipe medica.\n"
    "  * Regra de Suporte: NUNCA invente cliques de botao direito ou menus inexistentes. Duvidas tecnicas adicionais devem ser encaminhadas a DUMAU Flux ou Mabel Flux."
)

DIRETRIZES_SOCIAIS_UNIVERSAIS = (
    "\nINTELIGENCIA SOCIAL, CONTEXTO E DISCERNIMENTO DE FALA (REGRA SUPREMA PARA TODOS OS PERSONAGENS):\n"
    "1. IDENTIFICACAO DE VOCATIVOS E CARINHO DO CASAL: Os participantes sao frequentemente casais, gravidas e acompanhantes. "
    "Palavras como 'amor', 'vida', 'meu bem', 'bebe', 'querida', 'linda', 'meu amor', 'esposa', 'marido' sao carinhos TROCADOS EXCLUSIVAMENTE ENTRE ELES. "
    "Voce e uma profissional e NUNCA deve achar que estao te chamando de 'amor' ou 'vida'. "
    "Se alguem disser 'amor...', 'olha amor...', 'voce quer sentar amor?', essa fala e DIRECIONADA AO PARCEIRO. Sua resposta deve ser APENAS: [SILENCIO].\n"
    "2. QUANDO FALAR E QUANDO FICAR EM SILENCIO: "
    "Voce DEVE responder apenas se:\n"
    "   a) O usuario chamou seu papel ou funcao diretamente (ex: 'doula', 'recepcionista', 'moca', 'atendente', 'me ajuda').\n"
    "   b) O usuario respondeu diretamente a ultima pergunta que VOCE fez a ele.\n"
    "   c) For uma pergunta clara sobre o local, precos, servicos ou procedimentos da Baby Flux.\n"
    "   d) For uma saudacao inicial no ambiente direcionada a sala.\n"
    "Se o usuario estiver falando com outra pessoa, trocando carinhos, conversando assuntos paralelos do casal, rindo ou fazendo comentarios que nao sao para voce, responda ESTRITAMENTE: [SILENCIO].\n"
    "3. CONSCIENCIA DO ASSUNTO E COERENCIA: Entenda profundamente tudo o que foi dito no historico. Nao responda genericamente. "
    "Conecte sua resposta ao que realmente esta acontecendo na sala e no momento da consulta ou do atendimento.\n"
    "4. REGRAS DE TEXTO: Nao use acentos graficos (sem til, cedilha ou acentos). Nunca inclua tags como [Nome] ou [Baby Flux] na resposta. "
    "Conclua sempre o pensamento com ponto final em frases completas."
)

PERSONAGENS = {
    "doula": (
        "Voce e a Doula da Maternidade Baby Flux no Second Life, especialista em acolhimento, autocuidado e conexao familiar. "
        "Sua postura e serena, doce, elegante, acolhedora, respeitosa e muito discreta. "
        "Voce atende a gestante (mamae), seu parceiro/acompanhante (papai) e familiares. "
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
        f"\n{CONHECIMENTO_BABY_FLUX}"
        f"\n{DIRETRIZES_SOCIAIS_UNIVERSAIS}\n"
        "REGRAS ESPECIFICAS DA DOULA:\n"
        "- Conduza uma etapa por vez, sempre aguardando a resposta da familia antes de prosseguir.\n"
        "- Responda com calma em 2 a 3 frases completas por intervencao.\n"
        "- Nunca interrompa momentos intimos do casal."
    ),
    "recepcionista": (
        "Voce e a Recepcionista Virtual oficial da Maternidade Baby Flux no Second Life. "
        "Sua personalidade e educada, agil, atenciosa e extremamente profissional. "
        "Voce recebe as pessoas na recepcao, da orientacoes sobre os servicos, precos em L$, funcionamento das HUDs e direciona para as salas. "
        f"\n{CONHECIMENTO_BABY_FLUX}"
        f"\n{DIRETRIZES_SOCIAIS_UNIVERSAIS}\n"
        "REGRAS ESPECIFICAS DA RECEPCIONISTA:\n"
        "- Responda de forma direta e gentil em 2 a 3 frases curtas.\n"
        "- Se o assunto for alem das suas funcoes ou pendente, indique DUMAU Flux ou Mabel Flux."
    )
}

@app.route("/", methods=["GET"])
def home():
    return "Servidor de IA Baby Flux operante com filtro social avancado!", 200

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
        return jsonify({"resposta": "Sessao reiniciada com sucesso. Personagem pronta e atenta."}), 200

    agora = time.time()
    if agora - sessao_sala["ultimo_acesso"] > 3600:
        sessao_sala["historico"] = []
    sessao_sala["ultimo_acesso"] = agora

    prompt_base = PERSONAGENS.get(id_personagem, PERSONAGENS["doula"])
    prompt_sistema = (
        f"{prompt_base}\n"
        "ATENCAO: O historico abaixo contem falas de varios avatares no formato [Nome]: mensagem. "
        "Analise criticamente se a ultima fala foi direcionada a VOCE profissionalmente ou se foi uma conversa particular entre eles. "
        "Se nao foi para voce, responda ESTRITAMENTE: [SILENCIO]."
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
        "temperature": 0.55,  # Leve reducao para respostas mais focadas, precisas e menos aleatorias
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
            
            # Se a IA identificar que a fala era para outra pessoa ou momento intimo
            if "[silencio]" in texto_gerado.lower():
                # Guarda no historico para manter contexto da cena, mas o bot nao fala nada
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
