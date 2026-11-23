"""
Ferramentas da RAI — é aqui que ele vira um AGENTE: funções reais que o Claude decide quando usar.

Para criar uma nova ferramenta:
  1. escreva um método `_minha_ferramenta(self, ...)`
  2. adicione a descrição dela em DEFINICOES (nome, descrição e parâmetros)
O Claude lê as descrições e chama a função quando fizer sentido.
"""
import json
import os
import subprocess
import threading
import webbrowser
from datetime import datetime
from pathlib import Path

PASTA = Path(__file__).parent / "dados"
PASTA.mkdir(exist_ok=True)
ARQ_TAREFAS = PASTA / "tarefas.json"
ARQ_MEMORIA = PASTA / "memoria.json"

DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]

DEFINICOES = [
    {
        "name": "obter_data_hora",
        "description": "Retorna a data, a hora e o dia da semana atuais.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "criar_timer",
        "description": "Cria um timer que avisa em voz alta quando terminar.",
        "input_schema": {
            "type": "object",
            "properties": {
                "segundos": {"type": "integer", "description": "Duração em segundos"},
                "rotulo": {"type": "string", "description": "Nome curto, ex.: 'café'"},
            },
            "required": ["segundos"],
        },
    },
    {
        "name": "abrir_site",
        "description": "Abre um site no navegador padrão. Use a URL completa (https://...). "
                       "Para buscar algo no YouTube ou Google, monte a URL de busca.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        },
    },
    {
        "name": "abrir_app",
        "description": "Abre um aplicativo do Windows pelo nome (ex.: 'bloco de notas', 'calculadora', 'vscode', 'spotify').",
        "input_schema": {
            "type": "object",
            "properties": {"nome": {"type": "string"}},
            "required": ["nome"],
        },
    },
    {
        "name": "adicionar_tarefa",
        "description": "Adiciona uma tarefa na lista de tarefas do usuário (salva em disco).",
        "input_schema": {
            "type": "object",
            "properties": {"texto": {"type": "string"}},
            "required": ["texto"],
        },
    },
    {
        "name": "listar_tarefas",
        "description": "Lista as tarefas do usuário, numeradas, com status.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "concluir_tarefa",
        "description": "Marca uma tarefa como concluída pelo número dela na lista.",
        "input_schema": {
            "type": "object",
            "properties": {"numero": {"type": "integer"}},
            "required": ["numero"],
        },
    },
    {
        "name": "lembrar",
        "description": "Guarda um fato duradouro sobre o usuário para lembrar nas próximas conversas "
                       "(preferências, nomes, rotinas). Use quando ele pedir para lembrar algo.",
        "input_schema": {
            "type": "object",
            "properties": {"fato": {"type": "string"}},
            "required": ["fato"],
        },
    },
    {
        "name": "executar_powershell",
        "description": "Executa um comando PowerShell no computador do usuário e retorna a saída. "
                       "O usuário precisa confirmar antes. Use para consultas do sistema "
                       "(espaço em disco, IP, processos, bateria) ou tarefas que ele pedir.",
        "input_schema": {
            "type": "object",
            "properties": {
                "comando": {"type": "string"},
                "motivo": {"type": "string", "description": "Explicação curta do que o comando faz"},
            },
            "required": ["comando", "motivo"],
        },
    },
]


class Ferramentas:
    def __init__(self, apps, avisar, confirmar, pesquisa_web=True):
        """
        avisar(msg)        → função chamada quando um timer termina
        confirmar(pergunta) → função que retorna True/False (confirmação do usuário)
        """
        self.apps = {k.lower(): v for k, v in apps.items()}
        self.avisar = avisar
        self.confirmar = confirmar
        self.definicoes = list(DEFINICOES)
        if pesquisa_web:
            # Ferramenta de pesquisa executada pela própria Anthropic (não precisa de código aqui)
            self.definicoes.append({"type": "web_search_20250305", "name": "web_search", "max_uses": 3})

    def executar(self, nome, entrada):
        func = getattr(self, "_" + nome, None)
        if not func:
            return f"Erro: ferramenta '{nome}' não existe."
        try:
            return func(**(entrada or {}))
        except Exception as e:
            return f"Erro ao executar {nome}: {e}"

    # ── ferramentas ────────────────────────────────────────────

    def _obter_data_hora(self):
        a = datetime.now()
        return f"{DIAS[a.weekday()]}, {a.day} de {MESES[a.month-1]} de {a.year}, {a:%H:%M}"

    def _criar_timer(self, segundos, rotulo="timer"):
        segundos = max(1, int(segundos))
        t = threading.Timer(segundos, self.avisar, args=[f"O timer {rotulo} terminou."])
        t.daemon = True
        t.start()
        return f"Timer '{rotulo}' de {segundos} segundos iniciado."

    def _abrir_site(self, url):
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        webbrowser.open(url)
        return f"Abri {url}."

    def _abrir_app(self, nome):
        alvo = self.apps.get(nome.lower().strip(), nome)
        os.startfile(alvo) if ":" in alvo else subprocess.Popen(alvo, shell=True)
        return f"Abrindo {nome}."

    def _adicionar_tarefa(self, texto):
        tarefas = _ler(ARQ_TAREFAS, [])
        tarefas.append({"texto": texto, "feita": False, "criada": datetime.now().isoformat(timespec="minutes")})
        _salvar(ARQ_TAREFAS, tarefas)
        return f"Tarefa adicionada. Agora são {len(tarefas)} na lista."

    def _listar_tarefas(self):
        tarefas = _ler(ARQ_TAREFAS, [])
        if not tarefas:
            return "A lista de tarefas está vazia."
        return "\n".join(f"{i}. {t['texto']} [{'feita' if t['feita'] else 'pendente'}]"
                         for i, t in enumerate(tarefas, 1))

    def _concluir_tarefa(self, numero):
        tarefas = _ler(ARQ_TAREFAS, [])
        if not 1 <= int(numero) <= len(tarefas):
            return "Número de tarefa inválido."
        tarefas[int(numero) - 1]["feita"] = True
        _salvar(ARQ_TAREFAS, tarefas)
        return f"Tarefa {numero} concluída."

    def _lembrar(self, fato):
        mem = _ler(ARQ_MEMORIA, [])
        mem.append(fato)
        _salvar(ARQ_MEMORIA, mem)
        return "Guardado na memória."

    def _executar_powershell(self, comando, motivo=""):
        if not self.confirmar(f"A RAI quer rodar este comando ({motivo}):\n    {comando}\n  Permitir? [s/N] "):
            return "O usuário NÃO autorizou o comando."
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", comando],
            capture_output=True, text=True, timeout=60, encoding="utf-8", errors="replace",
        )
        saida = (r.stdout or "") + (("\nERRO: " + r.stderr) if r.stderr else "")
        return saida.strip()[:3000] or "(comando executado, sem saída)"


def memorias():
    return _ler(ARQ_MEMORIA, [])


def _ler(arq, padrao):
    try:
        return json.loads(arq.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return padrao


def _salvar(arq, dados):
    arq.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
