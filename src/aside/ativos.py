"""Baixa modelo e fontes no primeiro uso."""

import os
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "aside"
FONTES = Path.home() / ".local/share/fonts"

MODELO_URL = (
    "https://huggingface.co/handy-computer/parakeet-unified-en-0.6b-gguf/resolve/main/"
    "parakeet-unified-en-0.6b-Q5_K_M.gguf"
)
MODELO_NOME = "parakeet-unified-en-0.6b-Q5_K_M.gguf"

_OFL = "https://github.com/google/fonts/raw/main/ofl/"

FONTES_URL = {
    "SchibstedGrotesk.ttf": _OFL + "schibstedgrotesk/SchibstedGrotesk%5Bwght%5D.ttf",
    "InstrumentSerif-Regular.ttf": _OFL + "instrumentserif/InstrumentSerif-Regular.ttf",
}


def _baixar(url: str, destino: Path, rotulo: str) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    parcial = destino.with_suffix(destino.suffix + ".parcial")
    with urllib.request.urlopen(url, timeout=60) as r:
        total = int(r.headers.get("Content-Length", 0))
        lido = 0
        with open(parcial, "wb") as f:
            while bloco := r.read(1 << 20):
                f.write(bloco)
                lido += len(bloco)
                if total:
                    print(
                        f"\r{rotulo}: {100 * lido // total}%", end="", file=sys.stderr, flush=True
                    )
        print(file=sys.stderr)
    parcial.rename(destino)


def modelo() -> Path:
    destino = RAIZ / MODELO_NOME
    if not destino.exists():
        _baixar(MODELO_URL, destino, "modelo 516MB")
    return destino


def fontes() -> None:
    """Fonte é cosmético: se o download falhar, o GTK cai no system-ui e o app roda igual."""
    for nome, url in FONTES_URL.items():
        destino = FONTES / nome
        if destino.exists():
            continue
        try:
            _baixar(url, destino, nome)
        except OSError as e:
            print(f"fonte {nome} nao baixou: {e}", file=sys.stderr)


if __name__ == "__main__":
    print(modelo())
    fontes()
