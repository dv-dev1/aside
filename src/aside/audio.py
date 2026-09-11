"""Captura o áudio que sai do fone, que é o áudio dos outros participantes."""

import argparse
import os
import subprocess
import sys
import threading
from array import array
from collections import deque
from collections.abc import Iterator

TAXA = 16000
TAXA_CAPTURA = 48000
FATOR = TAXA_CAPTURA // TAXA
QUADRO = 1600
LIMIAR_SILENCIO = 350
LATENCIA_MS = 20


def reduzir(bruto: bytes) -> bytes:
    """Pedir 16000 Hz ao PipeWire mete um resampler que entrega em lotes de 2 segundos.
    Capturar em 48000 e reduzir aqui custa alguns ms e devolve a latência inteira."""
    a = array("h")
    a.frombytes(bruto)
    return array("h", [sum(a[i : i + FATOR]) // FATOR for i in range(0, len(a), FATOR)]).tobytes()


def sink_padrao() -> str:
    escolhido = os.environ.get("ASIDE_SINK")
    if escolhido:
        return escolhido
    return subprocess.run(
        ["pactl", "get-default-sink"], capture_output=True, text=True, check=True
    ).stdout.strip()


def rms(quadro: bytes) -> float:
    amostras = array("h")
    amostras.frombytes(quadro)
    if not amostras:
        return 0.0
    return (sum(a * a for a in amostras) / len(amostras)) ** 0.5


def mudo(quadro: bytes) -> bool:
    return rms(quadro) < LIMIAR_SILENCIO


class Recente:
    """Guarda só os últimos segundos capturados. Legenda ao vivo prefere perder um
    trecho a ficar meio minuto atrás da conversa: quando a fila enche, o quadro mais
    velho cai e quem consome descobre pelo `perdeu` que precisa recomeçar o fluxo."""

    def __init__(self, quadros_max: int):
        self._fila: deque[bytes] = deque(maxlen=quadros_max)
        self._sino = threading.Condition()
        self.perdeu = False

    def por(self, quadro: bytes) -> None:
        with self._sino:
            if len(self._fila) == self._fila.maxlen:
                self.perdeu = True
            self._fila.append(quadro)
            self._sino.notify()

    def pegar(self) -> bytes:
        with self._sino:
            while not self._fila:
                self._sino.wait()
            return self._fila.popleft()

    def reconheceu_perda(self) -> bool:
        perdeu, self.perdeu = self.perdeu, False
        return perdeu


class Porta:
    """Alimentar o modelo com silêncio custa o mesmo que alimentar fala e não produz
    palavra nenhuma: o atraso acumula até a legenda ficar segundos atrás da conversa."""

    def __init__(self, preroll: int = 2):
        self._anteriores: deque[bytes] = deque(maxlen=preroll)
        self.falando = False

    def passar(self, quadro: bytes) -> list[bytes]:
        if self.falando:
            return [quadro]
        if mudo(quadro):
            self._anteriores.append(quadro)
            return []
        self.falando = True
        saida = [*self._anteriores, quadro]
        self._anteriores.clear()
        return saida

    def reiniciar(self) -> None:
        self.falando = False
        self._anteriores.clear()


def quadros(sink: str | None = None) -> Iterator[bytes]:
    """O monitor do sink é o que sai do alto-falante. Minha voz vai para o microfone,
    então não entra aqui e a legenda fica só do outro lado."""
    alvo = f"{sink or sink_padrao()}.monitor"
    p = subprocess.Popen(
        [
            "parec",
            f"--device={alvo}",
            "--format=s16le",
            f"--rate={TAXA_CAPTURA}",
            "--channels=1",
            "--raw",
            f"--latency-msec={LATENCIA_MS}",
        ],
        stdout=subprocess.PIPE,
    )
    try:
        while True:
            bruto = p.stdout.read(QUADRO * FATOR * 2)
            if len(bruto) < QUADRO * FATOR * 2:
                return
            yield reduzir(bruto)
    finally:
        p.terminate()


def pcm_float(quadro: bytes) -> list[float]:
    amostras = array("h")
    amostras.frombytes(quadro)
    return [a / 32768.0 for a in amostras]


def main() -> int:
    ap = argparse.ArgumentParser(prog="aside.audio")
    ap.add_argument("--segundos", type=float, default=3.0)
    ap.add_argument("--rms", action="store_true")
    args = ap.parse_args()

    limite = int(args.segundos * TAXA / QUADRO)
    pico = 0.0
    for i, q in enumerate(quadros()):
        pico = max(pico, rms(q))
        if i + 1 >= limite:
            break
    if args.rms:
        print(f"rms pico: {pico:.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
