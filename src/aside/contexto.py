"""Quem você é e com quem vai falar. Mora fora do repositório: tem dado pessoal."""

import os
from pathlib import Path

PASTA = Path(os.environ.get("ASIDE_CONTEXTO", Path.home() / ".config" / "aside"))


def carregar(pasta: Path = PASTA) -> str:
    if not pasta.is_dir():
        return ""
    return "\n\n".join(
        f"## {arquivo.stem}\n\n{arquivo.read_text().strip()}"
        for arquivo in sorted(pasta.glob("*.md"))
    )


def nomes(pasta: Path = PASTA) -> list[str]:
    return [a.stem for a in sorted(pasta.glob("*.md"))] if pasta.is_dir() else []
