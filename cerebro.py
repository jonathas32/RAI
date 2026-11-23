"""
Cérebro da RAI: conversa com a IA (Gemini ou Claude) e executa as ferramentas que ela pedir.
Escolha qual usar em config.py → CEREBRO.
"""
import os
import re
import threading
import time
from datetime import datetime

from ferramentas import DIAS, memorias


def criar_cerebro(cfg, ferramentas):
    if cfg.CEREBRO == "gemini":
        return CerebroGemini(cfg, ferramentas)
    if cfg.CEREBRO == "ollama":
        return CerebroOllama(cfg, ferramentas)
    return CerebroClaude(cfg, ferramentas)


def instrucoes(cfg, ferramentas=None):
    mem = memorias()
    bloco_mem = ("\nO que você sabe sobre o usuário:\n- " + "\n- ".join(mem)) if mem else ""
    return f"""Você é {cfg.NOME} (Rotildino Avelino Inteligência), a assistente pessoal de IA do usuário, que roda no computador dele, no estilo do JARVIS do Homem de Ferro.
Seu nome é {cfg.NOME}. Chame o usuário de "{cfg.TRATAMENTO}".

Como responder:
- Português do Brasil. Suas respostas são FALADAS em voz alta: vá direto ao ponto, em 1 a 3 frases curtas. Sem markdown, listas, emojis ou links.
- Precisão acima de tudo: responda exatamente o que foi perguntado. Se não tiver certeza ou não souber, diga isso em vez de inventar.
- Números, datas e nomes: só afirme se tiver certeza. A data e a hora atuais estão no fim destas instruções: use-as direto, sem ferramenta.
- Tom: educado, sereno, confiante, com uma pitada de ironia elegante. Nunca bajulador.
- Use suas ferramentas sempre que o pedido envolver hora, timers, abrir sites ou apps, tarefas, memória ou comandos do computador. Não invente resultados.
- Depois de usar uma ferramenta, confirme o que fez em poucas palavras.
- Para fatos atuais ou que você não sabe com certeza (resultados de jogos, notícias, cotações, clima, preços), use pesquisar_internet quando disponível. Nunca invente resultados.
- Se o pedido estiver ambíguo, faça UMA pergunta curta para esclarecer.
- Se não puder fazer algo, diga com charme que esse protocolo ainda não foi instalado.

Agora: {DIAS[datetime.now().weekday()]}, {datetime.now():%d/%m/%Y %H:%M}.{bloco_mem}"""


FALHOU = "Perdão, me enrolei com essa. Pode repetir de outro jeito?"


# ── Gemini (Google) ─────────────────────────────────────────────
class CerebroGemini:
    def __init__(self, cfg, ferramentas):
        from google import genai
        from google.genai import types
        self.types = types
        self.cfg = cfg
        self.ferramentas = ferramentas
        self.cliente = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY"),
            http_options=types.HttpOptions(
                timeout=int(getattr(cfg, "TEMPO_MAX_RESPOSTA_SEG", 15) * 1000),   # modelo travado → troca de modelo
                retry_options=types.HttpRetryOptions(attempts=1),                 # sem esperas escondidas
            ),
        )
        self._pensamento = {}          # modelo → modo de "pensamento" que funcionou
        self.historico = []
        self.modelos = self._descobrir_modelos()
        self.modelo_atual = self.modelos[0]
        print(f"  Cérebro: {self.modelo_atual}")
        if getattr(cfg, "ESCOLHER_MAIS_RAPIDO", True) and len(self.modelos) > 1:
            threading.Thread(target=self._escolher_mais_rapido, daemon=True).start()
        declaracoes = []
        for d in ferramentas.definicoes:
            if d.get("type") or d["name"] == "obter_data_hora":   # exclusivas do Claude / hora já vai no prompt
                continue
            decl = {"name": d["name"], "description": d["description"]}
            if d["input_schema"].get("properties"):
                decl["parameters"] = d["input_schema"]
            declaracoes.append(decl)
        if getattr(cfg, "PESQUISA_WEB_GEMINI", True):
            declaracoes.append({
                "name": "pesquisar_internet",
                "description": "Pesquisa no Google informações atuais ou que você não sabe com certeza: resultados de jogos, "
                               "notícias, cotações, clima, preços, horários de lojas, fatos recentes. Retorna um resumo com fontes.",
                "parameters": {"type": "object", "properties": {
                    "pergunta": {"type": "string", "description": "O que pesquisar, completo e específico (inclua datas se houver)"}},
                    "required": ["pergunta"]},
            })
        self.tools = [types.Tool(function_declarations=declaracoes)]

    def pensar(self, texto):
        t = self.types
        self.historico.append(t.Content(role="user", parts=[t.Part(text=texto)]))
        for _ in range(8):
            resp = self._gerar()
            if not resp.candidates or not resp.candidates[0].content:
                return FALHOU
            self.historico.append(resp.candidates[0].content)

            chamadas = resp.function_calls
            if chamadas:
                partes = []
                for c in chamadas:
                    entrada = dict(c.args or {})
                    print(f"  ⚙  {c.name} {entrada}")
                    if c.name == "pesquisar_internet":
                        saida = self._pesquisar(str(entrada.get("pergunta", texto)))
                    else:
                        saida = self.ferramentas.executar(c.name, entrada)
                    partes.append(t.Part.from_function_response(name=c.name, response={"resultado": str(saida)}))
                self.historico.append(t.Content(role="user", parts=partes))
                continue

            self._podar()
            return (resp.text or "").strip() or FALHOU
        return FALHOU

    # Modelos novos do Gemini "pensam" antes de responder, o que pode levar dezenas de segundos.
    # Para voz queremos resposta rápida: pedimos o mínimo de pensamento que o modelo aceitar.
    def _opcoes_pensamento(self, modelo):
        if not getattr(self.cfg, "RESPOSTA_RAPIDA", True):
            return [None]
        if re.search(r"gemini-(2\.5|2\.0|1\.)", modelo):
            return ["budget0", None]
        return ["minimal", "low", "budget0", None]

    def _config(self, modo):
        t = self.types
        pensar = None
        if modo in ("minimal", "low"):
            pensar = t.ThinkingConfig(thinking_level=modo.upper())
        elif modo == "budget0":
            pensar = t.ThinkingConfig(thinking_budget=0)
        return t.GenerateContentConfig(
            system_instruction=instrucoes(self.cfg, self.ferramentas), tools=self.tools,
            temperature=getattr(self.cfg, "TEMPERATURA", 0.3), thinking_config=pensar,
        )

    def _gerar(self):
        """Chama o Gemini. Se o modelo estiver lotado, travado ou desativado, tenta o próximo."""
        modelos = [self.modelo_atual] + [m for m in self.modelos if m != self.modelo_atual]
        ultimo_erro = None
        for modelo in modelos:
            opcoes = self._opcoes_pensamento(modelo)
            if modelo in self._pensamento:
                opcoes = [self._pensamento[modelo]]
            i, tentativas_503 = 0, 0
            while i < len(opcoes):
                modo = opcoes[i]
                t0 = time.time()
                try:
                    resp = self.cliente.models.generate_content(model=modelo, contents=self.historico, config=self._config(modo))
                    self._pensamento[modelo] = modo
                    if modelo != self.modelo_atual:
                        print(f"  {modelo} respondeu, vou continuar com ele.")
                        self.modelo_atual = modelo
                    if getattr(self.cfg, "MOSTRAR_TEMPOS", True):
                        print(f"  \033[90m[{modelo} · pensamento {modo or 'padrão'} · {time.time()-t0:.1f}s]\033[0m")
                    return resp
                except Exception as e:
                    ultimo_erro = e
                    msg = str(e)
                    if ("400" in msg or "INVALID_ARGUMENT" in msg) and ("think" in msg.lower() or "budget" in msg.lower()):
                        i += 1                                   # modelo não aceita esse modo: tenta o próximo modo
                        continue
                    if any(c in msg for c in ("503", "UNAVAILABLE", "500", "INTERNAL")) and tentativas_503 == 0:
                        tentativas_503 += 1
                        time.sleep(0.8)                          # tenta mais uma vez o mesmo modelo
                        continue
                    if "404" in msg or "NOT_FOUND" in msg:
                        self.modelos = [m for m in self.modelos if m != modelo]      # não tenta mais esse
                        for sugerido in re.findall(r"models/(gemini-[\w.\-]+)", msg):
                            if sugerido != modelo and sugerido not in modelos:
                                modelos.insert(modelos.index(modelo) + 1, sugerido)   # o Google indicou um modelo novo
                                self.modelos.insert(0, sugerido)
                    lento = ("timeout" in msg.lower() or "timed out" in msg.lower() or "504" in msg or "DEADLINE" in msg
                             or type(e).__name__.lower().endswith("timeout"))
                    if lento and tentativas_503 == 0 and len(modelos) == 1:
                        tentativas_503 += 1                      # só há um modelo: tenta de novo uma vez
                        continue
                    if lento or any(c in msg for c in ("503", "UNAVAILABLE", "500", "INTERNAL", "429", "RESOURCE_EXHAUSTED", "404", "NOT_FOUND")):
                        print(f"  {modelo} {'demorou demais' if lento else 'indisponível agora'}, tentando outro…")
                        break                                    # próximo modelo
                    raise                                        # chave errada etc.: não adianta trocar
        raise ultimo_erro

    def _pesquisar(self, pergunta):
        """Pesquisa no Google com o próprio Gemini (Google Search grounding) e devolve um resumo."""
        t = self.types
        hoje = datetime.now().strftime("%d/%m/%Y")
        prompt = (f"Hoje é {hoje}. Pesquise no Google e responda em português, com precisão e em no máximo 3 frases: {pergunta}\n"
                  "Inclua a data do fato. Se não encontrar a informação confirmada, diga que não encontrou.")
        ultimo = None
        for modelo in [self.modelo_atual] + [m for m in self.modelos if m != self.modelo_atual][:2]:
            try:
                t0 = time.time()
                resp = self.cliente.models.generate_content(
                    model=modelo, contents=prompt,
                    config=t.GenerateContentConfig(tools=[t.Tool(google_search=t.GoogleSearch())], temperature=0.2),
                )
                fontes = []
                try:
                    for ch in resp.candidates[0].grounding_metadata.grounding_chunks or []:
                        if ch.web and ch.web.title:
                            fontes.append(ch.web.title)
                except Exception:
                    pass
                print(f"  \033[90m[pesquisa · {modelo} · {time.time()-t0:.1f}s · fontes: {', '.join(fontes[:3]) or '—'}]\033[0m")
                return (resp.text or "Não encontrei resultado.") + (f"\nFontes: {', '.join(fontes[:3])}" if fontes else "")
            except Exception as e:
                ultimo = e
        return f"A pesquisa falhou: {str(ultimo)[:200]}"

    def _escolher_mais_rapido(self):
        """Mede a velocidade dos modelos disponíveis (em segundo plano) e passa a usar o mais rápido."""
        t = self.types
        teste = [t.Content(role="user", parts=[t.Part(text="Responda apenas: ok")])]
        tempos = {}
        for modelo in self.modelos[:5]:
            for modo in self._opcoes_pensamento(modelo):
                cfg_teste = t.GenerateContentConfig(max_output_tokens=10, thinking_config=(
                    t.ThinkingConfig(thinking_level=modo.upper()) if modo in ("minimal", "low") else
                    t.ThinkingConfig(thinking_budget=0) if modo == "budget0" else None))
                t0 = time.time()
                try:
                    self.cliente.models.generate_content(model=modelo, contents=teste, config=cfg_teste)
                    tempos[modelo] = time.time() - t0
                    self._pensamento[modelo] = modo
                    break
                except Exception as e:
                    if ("400" in str(e) or "INVALID_ARGUMENT" in str(e)) and ("think" in str(e).lower() or "budget" in str(e).lower()):
                        continue
                    break
        if not tempos:
            return
        rapido = min(tempos, key=tempos.get)
        resumo = " · ".join(f"{m} {s:.1f}s" for m, s in sorted(tempos.items(), key=lambda x: x[1]))
        print(f"\n  \033[90m[velocidade dos modelos: {resumo}]\033[0m")
        if rapido != self.modelo_atual:
            print(f"  \033[90m[passando a usar o mais rápido: {rapido}]\033[0m")
            self.modelo_atual = rapido

    def _descobrir_modelos(self):
        """Pergunta ao Google quais modelos esta chave pode usar e monta a lista do mais rápido ao mais esperto."""
        preferidos = list(getattr(self.cfg, "MODELOS_GEMINI", []))
        try:
            disponiveis = []
            for m in self.cliente.models.list():
                nome = (m.name or "").replace("models/", "")
                acoes = getattr(m, "supported_actions", None) or []
                if "generateContent" not in acoes or "flash" not in nome:
                    continue
                if any(x in nome for x in ("tts", "image", "audio", "live", "embedding", "exp", "native")):
                    continue
                disponiveis.append(nome)
        except Exception as e:
            print(f"  (não consegui listar os modelos do Gemini: {str(e)[:120]})")
            return preferidos or ["gemini-flash-lite-latest"]

        def versao(n):
            nums = re.findall(r"\d+(?:\.\d+)?", n)
            return float(nums[0]) if nums else 0.0

        def nota(n):   # lite primeiro (rápido), versão mais nova primeiro, "preview" por último
            return ("lite" not in n, "preview" in n, -versao(n), "latest" not in n, n)

        ordem = [m for m in preferidos if m in disponiveis]
        ordem += [m for m in sorted(disponiveis, key=nota) if m not in ordem]
        return ordem or preferidos or ["gemini-flash-lite-latest"]

    def _podar(self, maximo=30):
        if len(self.historico) <= maximo:
            return
        h = self.historico[-maximo:]
        while h and not (h[0].role == "user" and h[0].parts and h[0].parts[0].text):
            h.pop(0)
        self.historico = h


# ── Ollama (IA local, roda no seu PC) ────────────────────────────
class CerebroOllama:
    """Usa um modelo rodando no Ollama (https://ollama.com). Grátis, offline e sem limite de uso."""

    def __init__(self, cfg, ferramentas):
        import httpx
        self.cfg = cfg
        self.ferramentas = ferramentas
        self.url = getattr(cfg, "OLLAMA_URL", "http://localhost:11434").rstrip("/")
        self.modelo_atual = getattr(cfg, "OLLAMA_MODELO", "qwen2.5:7b")
        self.http = httpx.Client(timeout=httpx.Timeout(120.0, connect=5.0))
        self.historico = []
        self.sem_think = True          # pede para modelos "pensantes" (qwen3, deepseek-r1) não pensarem
        self.tools = [{"type": "function", "function": {
                          "name": d["name"], "description": d["description"], "parameters": d["input_schema"]}}
                      for d in ferramentas.definicoes if not d.get("type") and d["name"] != "obter_data_hora"]
        self._verificar()
        print(f"  Cérebro: Ollama · {self.modelo_atual}")
        threading.Thread(target=self._aquecer, daemon=True).start()

    def _verificar(self):
        try:
            tags = self.http.get(f"{self.url}/api/tags").json()
        except Exception:
            raise SystemExit(f"\n  O Ollama não está rodando em {self.url}.\n"
                             "  Instale em https://ollama.com, abra o Ollama e rode a RAI de novo.\n")
        nomes = [m.get("name", "") for m in tags.get("models", [])]
        if not any(n == self.modelo_atual or n.split(":")[0] == self.modelo_atual for n in nomes):
            raise SystemExit(f"\n  O modelo '{self.modelo_atual}' não está baixado no Ollama.\n"
                             f"  Abra um terminal e rode:  ollama pull {self.modelo_atual}\n"
                             f"  Modelos que você já tem: {', '.join(nomes) or 'nenhum'}\n")

    def _aquecer(self):
        """Carrega o modelo na memória logo ao ligar, para a primeira resposta não demorar."""
        try:
            self.http.post(f"{self.url}/api/chat", json={"model": self.modelo_atual, "messages": [],
                                                          "keep_alive": getattr(self.cfg, "OLLAMA_MANTER_CARREGADO", "60m")})
        except Exception:
            pass

    def _chamar(self):
        corpo = {
            "model": self.modelo_atual,
            "messages": [{"role": "system", "content": instrucoes(self.cfg, self.ferramentas)}] + self.historico,
            "tools": self.tools,
            "stream": False,
            "keep_alive": getattr(self.cfg, "OLLAMA_MANTER_CARREGADO", "60m"),
            "options": {"temperature": getattr(self.cfg, "TEMPERATURA", 0.3)},
        }
        if self.sem_think:
            corpo["think"] = False
        t0 = time.time()
        r = self.http.post(f"{self.url}/api/chat", json=corpo)
        if r.status_code == 400 and "think" in r.text.lower() and self.sem_think:
            self.sem_think = False                      # modelo/versão não aceita o parâmetro: tenta sem
            return self._chamar()
        if r.status_code == 400 and "tool" in r.text.lower() and self.tools:
            print(f"  ({self.modelo_atual} não suporta ferramentas; seguindo só com conversa)")
            self.tools = []
            return self._chamar()
        if r.status_code >= 400:
            raise RuntimeError(f"Ollama {r.status_code}: {r.text[:300]}")
        if getattr(self.cfg, "MOSTRAR_TEMPOS", True):
            print(f"  \033[90m[ollama · {self.modelo_atual} · {time.time()-t0:.1f}s]\033[0m")
        return r.json().get("message", {})

    def pensar(self, texto):
        self.historico.append({"role": "user", "content": texto})
        for _ in range(6):
            msg = self._chamar()
            chamadas = msg.get("tool_calls") or []
            self.historico.append({"role": "assistant", "content": msg.get("content", ""),
                                   **({"tool_calls": chamadas} if chamadas else {})})
            if chamadas:
                for c in chamadas:
                    f = c.get("function", {})
                    nome, args = f.get("name", ""), f.get("arguments") or {}
                    if isinstance(args, str):
                        try:
                            import json
                            args = json.loads(args)
                        except Exception:
                            args = {}
                    print(f"  ⚙  {nome} {args}")
                    saida = self.ferramentas.executar(nome, args)
                    self.historico.append({"role": "tool", "content": str(saida), "tool_name": nome, "name": nome})
                continue
            self._podar()
            texto = re.sub(r"<think>.*?</think>", "", msg.get("content", ""), flags=re.S).strip()
            return texto or FALHOU
        return FALHOU

    def _podar(self, maximo=30):
        if len(self.historico) <= maximo:
            return
        h = self.historico[-maximo:]
        while h and h[0]["role"] != "user":
            h.pop(0)
        self.historico = h


# ── Claude (Anthropic) ──────────────────────────────────────────
class CerebroClaude:
    def __init__(self, cfg, ferramentas):
        import anthropic
        self.cfg = cfg
        self.ferramentas = ferramentas
        self.cliente = anthropic.Anthropic()   # lê ANTHROPIC_API_KEY
        self.historico = []

    def pensar(self, texto):
        self.historico.append({"role": "user", "content": texto})
        for _ in range(8):
            resp = self.cliente.messages.create(
                model=self.cfg.MODELO_CLAUDE,
                max_tokens=1024,
                temperature=getattr(self.cfg, "TEMPERATURA", 0.3),
                system=instrucoes(self.cfg, self.ferramentas),
                tools=self.ferramentas.definicoes,
                messages=self.historico,
            )
            self.historico.append({"role": "assistant", "content": resp.content})

            if resp.stop_reason == "tool_use":
                resultados = []
                for bloco in resp.content:
                    if bloco.type == "tool_use":
                        print(f"  ⚙  {bloco.name} {bloco.input}")
                        saida = self.ferramentas.executar(bloco.name, bloco.input)
                        resultados.append({"type": "tool_result", "tool_use_id": bloco.id, "content": str(saida)})
                self.historico.append({"role": "user", "content": resultados})
                continue

            if resp.stop_reason == "pause_turn":           # pesquisa web longa: deixa continuar
                continue

            self._podar()
            return "".join(b.text for b in resp.content if b.type == "text").strip() or FALHOU
        return FALHOU

    def _podar(self, maximo=30):
        if len(self.historico) <= maximo:
            return
        h = self.historico[-maximo:]
        while h and not (h[0]["role"] == "user" and isinstance(h[0]["content"], str)):
            h.pop(0)
        self.historico = h
