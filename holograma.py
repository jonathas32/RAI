"""
Holograma da RAI: uma janela com o núcleo animado que reage ao que ela está fazendo.
Roda um mini servidor local (só no seu PC) e abre a página holograma.html numa janela própria.
"""
import json
import queue
import secrets
import time
import subprocess
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HTML = Path(__file__).with_name("holograma.html")


class Holograma:
    def __init__(self, porta=8765):
        self.dados = {"estado": "iniciando", "voce": "", "rai": "", "modelo": "", "historico": []}
        self.nivel_mic = lambda: 0.0
        self.entrada = queue.Queue()                 # mensagens digitadas no chat do holograma
        self.token = secrets.token_hex(16)           # só a página da RAI consegue enviar mensagens
        holo = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path.startswith("/estado"):
                    d = dict(holo.dados)
                    try:
                        d["nivel"] = float(holo.nivel_mic())
                    except Exception:
                        d["nivel"] = 0.0
                    corpo, tipo = json.dumps(d).encode(), "application/json"
                elif self.path in ("/", "/index.html"):
                    corpo = HTML.read_text(encoding="utf-8").replace("__TOKEN__", holo.token).encode()
                    tipo = "text/html; charset=utf-8"
                else:
                    self.send_response(404)
                    self.end_headers()
                    return
                self.send_response(200)
                self.send_header("Content-Type", tipo)
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(corpo)

            def do_POST(self):
                if self.path != "/mensagem" or self.headers.get("X-RAI-Token") != holo.token:
                    self.send_response(403)
                    self.end_headers()
                    return
                try:
                    tamanho = min(int(self.headers.get("Content-Length", 0)), 8000)
                    texto = str(json.loads(self.rfile.read(tamanho) or b"{}").get("texto", "")).strip()[:2000]
                except Exception:
                    texto = ""
                if texto:
                    holo.entrada.put(texto)
                self.send_response(204)
                self.end_headers()

            def log_message(self, *args):   # silencia o log no terminal
                pass

        for p in range(porta, porta + 10):   # se a porta estiver ocupada, tenta a próxima
            try:
                self.servidor = ThreadingHTTPServer(("127.0.0.1", p), Handler)
                break
            except OSError:
                continue
        self.url = f"http://127.0.0.1:{self.servidor.server_address[1]}/"
        threading.Thread(target=self.servidor.serve_forever, daemon=True).start()

    def abrir(self):
        """Abre o holograma numa janela sem barra de navegador (modo app do Edge/Chrome)."""
        try:
            subprocess.Popen(f'start "" msedge --app={self.url} --window-size=1000,800', shell=True)
        except Exception:
            webbrowser.open(self.url)

    # ── chamados pelo main.py ──────────────────────────────────
    def estado(self, e):
        """iniciando · aguardando · ativo · pensando · falando · erro"""
        self.dados["estado"] = e

    def voce(self, texto, historico=True):
        self.dados["voce"] = texto[:200]
        if historico:
            self._registrar("voce", texto)

    def rai(self, texto):
        self.dados["rai"] = texto[:400]
        self._registrar("rai", texto)

    def _registrar(self, quem, texto):
        h = self.dados["historico"]
        h.append({"quem": quem, "texto": texto[:2000], "hora": time.strftime("%H:%M")})
        del h[:-50]                                  # guarda as últimas 50 mensagens

    def modelo(self, texto):
        self.dados["modelo"] = texto


class HologramaDesligado:
    """Usado quando HOLOGRAMA = False: aceita as mesmas chamadas e não faz nada."""
    nivel_mic = None
    def __init__(self):
        self.dados = {}
        self.entrada = queue.Queue()
    def abrir(self): pass
    def estado(self, e): pass
    def voce(self, t, historico=True): pass
    def rai(self, t): pass
    def modelo(self, t): pass
