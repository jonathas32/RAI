"""
RAI — Rotildino Avelino Inteligência
Assistente pessoal de IA por voz, com holograma.

Rode com:  python main.py     (ou dê dois cliques em iniciar.bat)
"""
import os
import queue
import re
import sys
import threading
import time
import unicodedata

from dotenv import load_dotenv

import config as cfg
from cerebro import criar_cerebro
from ferramentas import Ferramentas
from voz import Voz

CIANO, CINZA, AMARELO, RESET = "\033[96m", "\033[90m", "\033[93m", "\033[0m"

# Como o Whisper costuma escrever "RAI" falado (em português o R inicial soa como "H": "Hai")
WAKE = re.compile(r"\b(r\s?a\s?i|rai|ray|rae|rhai|hai|hay|rahi|rahy)\b")
# No começo da frase o Whisper às vezes escreve "RAI" como "Ai" ou "Oi"
WAKE_INICIO = re.compile(r"^\s*(ai|oi)\b")
DORMIR = ("pode descansar", "dispensada", "dispensado", "boa noite rai", "obrigado rai", "valeu rai")


def _norm_char(c):
    c = unicodedata.normalize("NFD", c.lower())[0]
    return c if (c.isalnum() or c in " -_") else " "


def normalizar(t):
    """minúsculas, sem acentos e sem pontuação (mesmo tamanho do texto original)."""
    return "".join(_norm_char(c) for c in t)


def detectar_chamado(texto):
    """Retorna (foi_chamada, comando_sem_o_nome), preservando acentos do comando."""
    norm = normalizar(texto)
    m = WAKE.search(norm) or WAKE_INICIO.search(norm)
    if not m:
        return False, texto
    resto = (texto[:m.start()] + " " + texto[m.end():]).strip(" ,.-!?")
    return True, re.sub(r"\s+", " ", resto)


def confirmar(pergunta):
    print(f"\n  {AMARELO}{pergunta}{RESET}", end="")
    return input().strip().lower() in ("s", "sim", "y")


def explicar_erro(erro):
    """Transforma o erro técnico numa frase que diz o que fazer."""
    e, t = erro.lower(), cfg.TRATAMENTO
    if cfg.CEREBRO == "ollama":
        if "connect" in e or "refused" in e:
            return f"O Ollama parou de responder, {t}. Verifique se ele está aberto."
        if "timeout" in e or "timed out" in e:
            return f"O modelo local demorou demais, {t}. Tente um modelo menor no config."
    if "api_key_invalid" in e or "api key not valid" in e or "api key expired" in e or "401" in e:
        return f"Minha chave do Gemini foi recusada, {t}. Gere uma nova no AI Studio e cole no arquivo ponto env."
    if "permission_denied" in e or "403" in e:
        return f"O Gemini negou acesso com esta chave, {t}. Confira se a chave é do AI Studio e se a API está ativa."
    if "429" in e or "resource_exhausted" in e or "quota" in e:
        return f"Atingi o limite de uso gratuito por enquanto, {t}. Aguarde um minuto."
    if "504" in e or "deadline" in e:
        return f"O Gemini demorou demais para responder, {t}. Os servidores gratuitos estão lentos agora; tente de novo."
    if "503" in e or "unavailable" in e or "overloaded" in e:
        return f"Os servidores do Gemini estão congestionados agora, {t}. Tente de novo em alguns segundos."
    if "404" in e or "not_found" in e:
        return f"Nenhum dos modelos configurados foi encontrado, {t}. Confira a lista de modelos no config."
    if "ssl" in e or "certificate" in e:
        return f"A conexão segura com o Gemini foi bloqueada, {t}. Pode ser o antivírus ou o proxy da rede."
    if "connect" in e or "getaddrinfo" in e or "timed out" in e or "timeout" in e or "network" in e:
        return f"Não consegui alcançar o servidor do Gemini, {t}. Verifique a internet ou o firewall."
    return f"Tive um erro inesperado, {t}. Os detalhes estão no terminal e no arquivo rai erros ponto log."


MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]
DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]


ENCHIMENTO = {"me", "diz", "diga", "fala", "por", "favor", "agora", "ai", "oi", "entao", "voce", "sabe", "pode", "dizer",
              "falar", "qual", "e", "o", "a", "de", "da", "do"}
PERGUNTAS_HORA = {"que horas", "que horas sao", "quantas horas", "quantas horas sao", "que hora", "horas", "horario", "hora"}
PERGUNTAS_DATA = {"que dia", "que dia hoje", "dia hoje", "que dia estamos", "data hoje", "que data hoje", "hoje que dia", "data",
                  "dia semana hoje", "que dia semana", "que dia semana hoje", "hoje que dia semana"}


def resposta_instantanea(texto):
    """Perguntas simples (hora e data) respondidas na hora, sem ir até a IA: instantâneo e 100% preciso."""
    palavras = [p for p in normalizar(texto).split() if p not in ENCHIMENTO and p != "e"]
    frase = " ".join(palavras)
    agora = time.localtime()
    if frase in PERGUNTAS_HORA:
        h, m = agora.tm_hour, agora.tm_min
        hora = f"{h} hora{'s' if h != 1 else ''}" if h else "meia-noite"
        return f"São {hora}{f' e {m} minuto' + ('s' if m != 1 else '') if m else ' em ponto'}, {cfg.TRATAMENTO}."
    if frase in PERGUNTAS_DATA:
        return f"Hoje é {DIAS[agora.tm_wday]}, {agora.tm_mday} de {MESES[agora.tm_mon - 1]} de {agora.tm_year}, {cfg.TRATAMENTO}."
    return None


BANNER = f"""{CIANO}
   ██████╗  █████╗ ██╗
   ██╔══██╗██╔══██╗██║
   ██████╔╝███████║██║
   ██╔══██╗██╔══██║██║
   ██║  ██║██║  ██║██║
   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝   Rotildino Avelino Inteligência{RESET}
"""


def main():
    os.system("")                    # ativa cores no terminal do Windows
    load_dotenv()
    print(BANNER)

    var = {"gemini": "GEMINI_API_KEY", "claude": "ANTHROPIC_API_KEY"}.get(cfg.CEREBRO)
    chave = os.getenv(var, "") if var else "ollama-nao-precisa"
    if not chave or "cole" in chave or "coloque" in chave:
        print(f"  Falta a chave da API ({var}). Abra o arquivo .env e cole sua chave nele.")
        input("  Enter para sair.")
        return

    avisos = queue.Queue()
    if cfg.HOLOGRAMA:
        from holograma import Holograma
        holo = Holograma()
        holo.abrir()
        print(f"  {CINZA}Holograma aberto em {holo.url} (F11 = tela cheia){RESET}")
    else:
        from holograma import HologramaDesligado
        holo = HologramaDesligado()
    holo.modelo(cfg.CEREBRO.upper())

    voz = Voz(cfg.TTS_MOTOR, cfg.VOZ, cfg.VELOCIDADE, cfg.TOM)
    ferramentas = Ferramentas(cfg.APPS, avisar=avisos.put, confirmar=confirmar,
                              pesquisa_web=cfg.PESQUISA_WEB and cfg.CEREBRO == "claude")
    try:
        cerebro = criar_cerebro(cfg, ferramentas)
    except SystemExit as e:
        print(e)
        input("  Enter para sair.")
        return
    ouvido = None

    def dizer(texto, em_voz=True):
        """Fala em voz alta, atualizando o holograma e pausando o microfone."""
        holo.rai(texto)
        if not em_voz:
            return
        holo.estado("falando")
        if ouvido:
            ouvido.pausar()
        voz.falar(texto)
        if ouvido:
            ouvido.retomar()
        holo.estado("aguardando")

    def responder(texto, em_voz=True):
        rapida = resposta_instantanea(texto)
        if rapida:
            print(f"  {CIANO}{cfg.NOME}:{RESET} {rapida}  {CINZA}(instantânea){RESET}\n")
            dizer(rapida, em_voz)
            holo.estado("aguardando")
            return
        print(f"  {CINZA}…pensando{RESET}", end="\r")
        holo.estado("pensando")
        t0 = time.time()
        try:
            resposta = cerebro.pensar(texto)
        except Exception as e:
            erro = f"{type(e).__name__}: {e}"
            resposta = explicar_erro(erro)
            print(f"  {AMARELO}[erro] {erro[:500]}{RESET}")
            try:                                              # guarda o erro completo para consulta
                with open("rai_erros.log", "a", encoding="utf-8") as log:
                    log.write(f"{time.strftime('%d/%m/%Y %H:%M:%S')}  {erro}\n")
            except OSError:
                pass
            holo.voce(f"[erro] {erro[:160]}", historico=False)
        modelo = getattr(cerebro, "modelo_atual", None)
        if modelo:
            holo.modelo(modelo)
        print(f"  {CIANO}{cfg.NOME}:{RESET} {resposta}  {CINZA}({time.time()-t0:.1f}s){RESET}\n")
        dizer(resposta, em_voz)
        holo.estado("aguardando")

    def atender_digitado(texto):
        """Mensagem escrita no chat do holograma: não precisa dizer "RAI"."""
        print(f"  Você (chat): {texto}          ")
        holo.voce(texto)
        responder(texto, em_voz=cfg.FALAR_RESPOSTA_DO_CHAT)

    saudacao = f"Olá, {cfg.TRATAMENTO}. {cfg.NOME} online. É só me chamar."

    # ── modo texto ──────────────────────────────────────────────
    if cfg.MODO == "texto":
        trava = threading.Lock()

        def falar_avisos():
            while True:
                msg = avisos.get()
                print(f"\n  {AMARELO}⏰ {msg}{RESET}")
                with trava:
                    dizer(f"{cfg.TRATAMENTO.capitalize()}, {msg}")
        threading.Thread(target=falar_avisos, daemon=True).start()

        def atender_chat():
            while True:
                texto = holo.entrada.get()
                with trava:
                    atender_digitado(texto)
        threading.Thread(target=atender_chat, daemon=True).start()
        print(f"  {CIANO}{cfg.NOME}:{RESET} {saudacao}  (digite 'sair' para encerrar)\n")
        holo.estado("aguardando")
        dizer(saudacao)
        while True:
            texto = input("  Você: ").strip()
            if texto.lower() in ("sair", "exit"):
                break
            if texto:
                holo.voce(texto)
                with trava:
                    responder(texto)
        return

    # ── modo voz (estilo Alexa: sempre comece com "RAI") ────────
    from ouvido import Ouvido
    holo.estado("iniciando")
    ouvido = Ouvido(cfg.WHISPER_MODELO, cfg.SENSIBILIDADE_MIC, cfg.SILENCIO_FIM_SEG, cfg.NOME)
    holo.nivel_mic = lambda: ouvido.nivel
    print(f"\n  {CIANO}{cfg.NOME}:{RESET} {saudacao}")
    print(f"  {CINZA}Diga \"{cfg.NOME}, ...\" antes de cada pedido. Ctrl+C para encerrar.{RESET}\n")
    dizer(saudacao)

    escutando_ate = 0.0       # depois de "RAI" sozinho, aceita a próxima frase sem o nome
    while True:
        while not avisos.empty():                                  # timers que terminaram
            msg = avisos.get()
            print(f"  {AMARELO}⏰ {msg}{RESET}")
            dizer(f"{cfg.TRATAMENTO.capitalize()}, {msg}")

        while not holo.entrada.empty():                            # mensagens escritas no chat
            atender_digitado(holo.entrada.get())

        aberto = time.time() < escutando_ate
        holo.estado("ativo" if aberto else "aguardando")
        print(f"  {CINZA}{'● ouvindo seu pedido…' if aberto else f'○ aguardando \"{cfg.NOME}\"'}        {RESET}", end="\r")
        audio = ouvido.gravar_frase(espera=0.4)
        if audio is None:
            continue
        t_ouvir = time.time()
        texto = ouvido.transcrever(audio)
        t_ouvir = time.time() - t_ouvir
        if not texto:
            continue

        chamada, comando = detectar_chamado(texto)
        if not chamada and not aberto:
            print(f"  {CINZA}(ignorado, diga \"{cfg.NOME}\" antes) {texto}{RESET}          ")
            continue

        print(f"  Você: {texto}  {CINZA}(entendi em {t_ouvir:.1f}s){RESET}          ")
        holo.voce(texto)
        escutando_ate = 0.0

        if chamada and not comando.strip():                        # só "RAI" → espera o pedido
            dizer("Pois não?")
            escutando_ate = time.time() + cfg.ESPERA_PEDIDO_SEG
            continue

        if any(p in normalizar(texto) for p in DORMIR):
            dizer(f"Às ordens, {cfg.TRATAMENTO}.")
            continue

        responder(comando if chamada else texto)
        if cfg.JANELA_CONVERSA_SEG:
            escutando_ate = time.time() + cfg.JANELA_CONVERSA_SEG


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n  {CIANO}{cfg.NOME}:{RESET} Desligando. Até logo.")
        sys.exit(0)
