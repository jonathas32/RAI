"""
Ouvido da RAI: escuta o microfone, detecta quando você fala e transcreve com Whisper (local).
"""
import queue
import time

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

TAXA = 16000          # Whisper trabalha em 16 kHz
BLOCO = 480           # 30 ms por bloco


class Ouvido:
    def __init__(self, modelo="base", sensibilidade=3.0, silencio_fim=0.7, nome="RAI"):
        print(f"  Carregando reconhecimento de fala (Whisper '{modelo}')…")
        print("  (na primeira vez ele baixa o modelo; pode levar alguns minutos)")
        self.modelo = WhisperModel(modelo, device="cpu", compute_type="int8")
        self.sensibilidade = sensibilidade
        self.silencio_fim = silencio_fim
        self.nome = nome
        self.fila = queue.Queue()
        self.pausado = False
        self.nivel = 0.0               # volume atual do microfone (0 a ~1), usado pelo holograma
        self.stream = sd.InputStream(
            samplerate=TAXA, channels=1, dtype="float32",
            blocksize=BLOCO, callback=self._callback,
        )
        self.stream.start()
        self.limiar = self._calibrar()

    def _callback(self, indata, frames, tempo, status):
        if not self.pausado:
            bloco = indata[:, 0].copy()
            self.fila.put(bloco)
            self.nivel = min(1.0, _rms(bloco) * 12)
        else:
            self.nivel = 0.0

    def _calibrar(self, segundos=1.5):
        print("  Calibrando o microfone… fique em silêncio um instante.")
        niveis = []
        fim = time.time() + segundos
        while time.time() < fim:
            try:
                niveis.append(_rms(self.fila.get(timeout=1)))
            except queue.Empty:
                break
        ambiente = float(np.median(niveis)) if niveis else 0.003
        limiar = max(ambiente * self.sensibilidade, 0.008)
        print(f"  Microfone pronto (ruído {ambiente:.4f} · limiar {limiar:.4f}).")
        return limiar

    def pausar(self):
        """Para de ouvir (enquanto a RAI fala, para não ouvir a si mesmo)."""
        self.pausado = True

    def retomar(self):
        self._esvaziar()
        self.pausado = False

    def _esvaziar(self):
        while not self.fila.empty():
            try:
                self.fila.get_nowait()
            except queue.Empty:
                break

    def gravar_frase(self, espera=1.0, max_seg=15):
        """
        Espera alguém começar a falar (até `espera` segundos) e grava até um silêncio.
        Retorna o áudio (numpy) ou None se ninguém falou.
        """
        pre = []                       # um pouco de áudio antes da fala, para não cortar o início
        fim_espera = time.time() + espera
        ativos = 0
        while True:
            try:
                bloco = self.fila.get(timeout=0.2)
            except queue.Empty:
                if time.time() > fim_espera and ativos == 0:
                    return None
                continue
            pre.append(bloco)
            pre = pre[-10:]
            ativos = ativos + 1 if _rms(bloco) > self.limiar else 0
            if ativos >= 3:
                break
            if time.time() > fim_espera and ativos == 0:
                return None

        audio = list(pre)
        silencio = 0.0
        inicio = time.time()
        while time.time() - inicio < max_seg:
            try:
                bloco = self.fila.get(timeout=0.5)
            except queue.Empty:
                break
            audio.append(bloco)
            if _rms(bloco) < self.limiar:
                silencio += BLOCO / TAXA
                if silencio >= self.silencio_fim:
                    break
            else:
                silencio = 0.0
        return np.concatenate(audio)

    def transcrever(self, audio):
        segmentos, _ = self.modelo.transcribe(
            audio, language="pt", beam_size=1,
            initial_prompt=f"{self.nome}, assistente pessoal. {self.nome}, que horas são?",
            vad_filter=True,
        )
        return " ".join(s.text for s in segmentos).strip()


def _rms(bloco):
    return float(np.sqrt(np.mean(bloco ** 2)))
