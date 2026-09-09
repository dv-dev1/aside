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


class Transcritor:
    def __init__(self, caminho: Path | None = None, backend: str = BACKEND):
        try:
            self._modelo = tc.Model(str(caminho or ativos.modelo()), backend=backend)
        except tc.BackendError:
            self._modelo = tc.Model(str(caminho or ativos.modelo()), backend="cpu")
        self._sessao = tc.Session(self._modelo)
        self._fluxo = self._sessao.stream()

    def alimentar(self, pcm: list[float]) -> str:
        self._fluxo.feed(pcm)
        return self._fluxo.text().full

    def reiniciar(self) -> str:
        self._fluxo.finalize()
        final = self._fluxo.text().full
        self._fluxo = self._sessao.stream()
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
