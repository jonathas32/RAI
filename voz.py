"""
Voz da RAI: transforma texto em fala.
"""
import asyncio
import os
import re
import tempfile
import threading
import time


class Voz:
    def __init__(self, motor="edge", voz="pt-BR-AntonioNeural", velocidade="+0%", tom="+0Hz"):
        self.motor = motor
        self.voz = voz
        self.velocidade = velocidade
        self.tom = tom
        self.trava = threading.Lock()
        if motor != "edge":
            import pyttsx3
            self.engine = pyttsx3.init()
            for v in self.engine.getProperty("voices"):
                if "portug" in v.name.lower() or "brazil" in v.name.lower() or "pt" in (v.id or "").lower():
                    self.engine.setProperty("voice", v.id)
                    break

    def falar(self, texto):
        texto = _limpar(texto)
        if not texto:
            return
        with self.trava:
            try:
                if self.motor == "edge":
                    self._falar_edge(texto)
                else:
                    self.engine.say(texto)
                    self.engine.runAndWait()
            except Exception as e:  # sem internet, etc.
                print(f"  [voz] falhou: {e}")

    def _falar_edge(self, texto):
        """Gera a primeira frase, começa a tocar e já vai gerando a próxima (resposta começa mais rápido)."""
        frases = _frases(texto)
        arquivos = [None] * len(frases)

        def gerar(i):
            arquivos[i] = self._gerar_mp3(frases[i])

        gerar(0)
        for i in range(len(frases)):
            prox = None
            if i + 1 < len(frases):
                prox = threading.Thread(target=gerar, args=(i + 1,))
                prox.start()
            if arquivos[i]:
                _tocar_mp3(arquivos[i])
                try:
                    os.remove(arquivos[i])
                except OSError:
                    pass
            if prox:
                prox.join()

    def _gerar_mp3(self, frase):
        import edge_tts
        arq = os.path.join(tempfile.gettempdir(), f"rai_{time.time_ns()}.mp3")
        try:
            asyncio.run(edge_tts.Communicate(frase, self.voz, rate=self.velocidade, pitch=self.tom).save(arq))
            return arq
        except Exception as e:
            print(f"  [voz] falhou: {e}")
            return None


def _frases(texto):
    partes = [p.strip() for p in re.split(r"(?<=[.!?])\s+", texto) if p.strip()]
    # junta frases muito curtas para não picotar a fala
    saida = []
    for p in partes:
        if saida and len(saida[-1]) < 40:
            saida[-1] += " " + p
        else:
            saida.append(p)
    return saida or [texto]


def _tocar_mp3(arq):
    """Toca um MP3 usando o player embutido do Windows (sem instalar nada)."""
    import ctypes
    mci = ctypes.windll.winmm.mciSendStringW
    alias = f"raiv{time.time_ns() % 100000}"
    mci(f'open "{arq}" type mpegvideo alias {alias}', None, 0, None)
    mci(f"play {alias} wait", None, 0, None)
    mci(f"close {alias}", None, 0, None)


def _limpar(texto):
    """Remove markdown e links para a fala ficar natural."""
    texto = re.sub(r"https?://\S+", "o link", texto)
    texto = re.sub(r"[*_#`>\[\]]", "", texto)
    return texto.strip()
