"""Transcrição local em streaming, na GPU integrada."""

import argparse
import sys
import time
import wave
from array import array
from collections.abc import Iterator
from pathlib import Path

import transcribe_cpp as tc

from . import ativos

BACKEND = "vulkan"
TAXA = 16000

# O padrao do modelo espera 3,20s de audio antes da primeira palavra. Medido na grade
# que o proprio modelo aceita: 560/0 entrega a primeira palavra em 1,20s e roda a
# 2,24x tempo real. `chunk` e o que custa: 160 entrega 1,20s tambem, mas roda a 0,60x
# e atrasa 1s a cada 2s de fala, para sempre. Nunca mexer aqui sem medir vazao junto.
CHUNK_MS = 560
RIGHT_MS = 0


class Transcritor:
    def __init__(self, caminho: Path | None = None, backend: str = BACKEND):
        try:
            self._modelo = tc.Model(str(caminho or ativos.modelo()), backend=backend)
        except tc.BackendError:
            self._modelo = tc.Model(str(caminho or ativos.modelo()), backend="cpu")
        self._sessao = tc.Session(self._modelo)
        self._aquecer()
        self._fluxo = self._abrir()

    def _aquecer(self) -> None:
        """A primeira inferência custa vários segundos a mais que as seguintes, e sem
        isto ela cairia na primeira frase da reunião."""
        fluxo = self._abrir()
        fluxo.feed([0.0] * TAXA)
        fluxo.finalize()

    def _abrir(self):
        return self._sessao.stream(
            family=tc.ParakeetBufferedStreamOptions(chunk_ms=CHUNK_MS, right_ms=RIGHT_MS)
        )

    def alimentar(self, pcm: list[float]) -> str | None:
        """Devolve None quando nada mudou: quem chama evita redesenhar a barra à toa."""
        if not self._fluxo.feed(pcm).result_changed:
            return None
        return self._fluxo.text().full

    def reiniciar(self) -> str:
        self._fluxo.finalize()
        final = self._fluxo.text().full
        self._fluxo = self._abrir()
        return final

    def fechar(self) -> None:
        self._sessao.close()
        self._modelo.close()


def _pcm_do_wav(caminho: Path) -> tuple[list[float], int]:
    with wave.open(str(caminho)) as w:
        amostras = array("h")
        amostras.frombytes(w.readframes(w.getnframes()))
        return [a / 32768.0 for a in amostras], w.getframerate()


def marcos(caminho: Path, passo_s: float = 0.5) -> Iterator[tuple[float, str]]:
    pcm, taxa = _pcm_do_wav(caminho)
    t = Transcritor()
    passo = int(taxa * passo_s)
    inicio, anterior = time.time(), ""
    try:
        for i in range(0, len(pcm), passo):
            texto = t.alimentar(pcm[i : i + passo])
            if texto != anterior:
                anterior = texto
                yield time.time() - inicio, texto
        yield time.time() - inicio, t.reiniciar()
    finally:
        t.fechar()


def main() -> int:
    ap = argparse.ArgumentParser(prog="aside.stt")
    ap.add_argument("--arquivo", type=Path, required=True)
    ap.add_argument("--marcos", action="store_true")
    args = ap.parse_args()

    ultimo = ""
    for quando, texto in marcos(args.arquivo):
        ultimo = texto
        if args.marcos:
            print(f"{quando:5.2f}s  {texto}")
    if not args.marcos:
        print(ultimo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
