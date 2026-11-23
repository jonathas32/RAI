"""
Configurações da RAI. Edite à vontade.
"""

# ── Identidade ────────────────────────────────────────────────
NOME = "RAI"                   # Rotildino Avelino Inteligência
TRATAMENTO = "senhor"          # como a RAI chama você: "senhor", "chefe", seu nome...

# ── Cérebro ───────────────────────────────────────────────────
# "gemini" → Google, tem plano gratuito. Chave em https://aistudio.google.com  (GEMINI_API_KEY no .env)
# "claude" → Anthropic, pago.            Chave em https://console.anthropic.com (ANTHROPIC_API_KEY no .env)
# "ollama" → IA local no seu PC, grátis e offline. Instale em https://ollama.com (não precisa de chave)
CEREBRO = "gemini"

# ── Ollama (só vale com CEREBRO = "ollama") ───────────────────
# Baixe o modelo antes, no terminal:  ollama pull qwen2.5:7b
# Sugestões (precisam suportar "tools"): qwen2.5:7b (bom em português), llama3.1:8b, qwen2.5:3b (PC mais fraco)
OLLAMA_MODELO = "qwen2.5:7b"
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MANTER_CARREGADO = "60m"   # mantém o modelo na memória para responder rápido

# A RAI pergunta ao Google quais modelos a sua chave pode usar e escolhe sozinha
# (os "lite" primeiro, que são os mais rápidos). Se um estiver lotado, ela tenta o próximo.
# Se quiser forçar um modelo, coloque o nome aqui, ex.: ["gemini-3.0-flash"]. Vazio = automático.
MODELOS_GEMINI = []
TEMPERATURA = 0.3              # mais baixo = respostas mais precisas e consistentes
RESPOSTA_RAPIDA = True         # pede ao Gemini para "pensar" o mínimo (resposta em 1–3 s em vez de 20–40 s)
TEMPO_MAX_RESPOSTA_SEG = 25    # se um modelo travar por mais que isso, ela troca de modelo
MOSTRAR_TEMPOS = True          # mostra no terminal quanto cada resposta levou
ESCOLHER_MAIS_RAPIDO = True    # ao ligar, mede a velocidade dos modelos e usa o mais rápido

# Modelos Claude: https://docs.claude.com/en/docs/about-claude/models
MODELO_CLAUDE = "claude-haiku-4-5"
PESQUISA_WEB = True            # só no Claude: deixa a RAI pesquisar na internet (cobrança extra)
PESQUISA_WEB_GEMINI = True     # Gemini: pesquisa no Google para fatos atuais (jogos, notícias, cotações)

# ── Modo de uso ───────────────────────────────────────────────
# "voz"   → fica ouvindo; diga "RAI, ..." antes de cada pedido (igual Alexa)
# "texto" → você digita no terminal (bom para testar sem microfone)
MODO = "voz"

# ── Ouvido (reconhecimento de fala, roda local) ───────────────
# tiny / base / small / medium  → maior = entende melhor, porém mais lento
WHISPER_MODELO = "base"
SENSIBILIDADE_MIC = 3.0        # maior = precisa falar mais alto para ela começar a gravar
SILENCIO_FIM_SEG = 0.7         # quanto tempo de silêncio encerra sua frase

# Se você disser só "RAI", ela responde "Pois não?" e espera o pedido por este tempo.
ESPERA_PEDIDO_SEG = 8

# Depois de responder, aceitar a próxima frase SEM dizer "RAI"? 0 = não (sempre dizer "RAI", igual Alexa).
JANELA_CONVERSA_SEG = 0

# ── Voz (fala) ────────────────────────────────────────────────
# "edge"    → vozes neurais da Microsoft, bem naturais, grátis (precisa de internet)
# "offline" → voz do Windows (SAPI), funciona sem internet, mais robótica
TTS_MOTOR = "edge"
# Vozes pt-BR: pt-BR-AntonioNeural (masc.), pt-BR-FranciscaNeural (fem.), pt-BR-ThalitaNeural (fem.)
# Vozes que falam português com sotaque estrangeiro:
#   en-US-AndrewMultilingualNeural, en-US-BrianMultilingualNeural, en-GB-OllieMultilingualNeural
VOZ = "pt-BR-AntonioNeural"
VELOCIDADE = "+6%"             # ex.: "-10%", "+0%", "+15%"
TOM = "-6Hz"                   # mais grave = mais "IA de filme". Ex.: "-10Hz", "+0Hz"

# ── Apps que a RAI sabe abrir ("RAI, abre o bloco de notas") ──
# nome falado  →  comando do Windows
APPS = {
    "bloco de notas": "notepad",
    "calculadora": "calc",
    "explorador": "explorer",
    "paint": "mspaint",
    "terminal": "wt",
    "powershell": "powershell",
    "vscode": "code",
    "vs code": "code",
    "chrome": "chrome",
    "edge": "msedge",
    "spotify": "spotify:",
    "configurações": "ms-settings:",
}

# ── Holograma ─────────────────────────────────────────────────
HOLOGRAMA = True               # abre a janela com o núcleo animado (com caixa de chat para escrever)
FALAR_RESPOSTA_DO_CHAT = True  # quando você escreve no chat, ela também responde em voz alta?
