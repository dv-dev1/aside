"""Tradução e sugestão de resposta. Único módulo que abre rede."""

import json
import os
import urllib.request

MODELO = "gpt-4o-mini"
URL = "https://api.openai.com/v1/chat/completions"
SEM_CHAVE = "OPENAI_API_KEY nao definida — legenda em ingles continua, traducao off"

_TRADUZIR = "Traduza para portugues do Brasil. Responda so com a traducao, nada mais."
_SUGERIR = (
    "Voce ajuda alguem com ingles limitado numa reuniao. A partir do que a outra pessoa "
    "falou, escreva 3 respostas curtas em ingles simples que ele pode falar em voz alta. "
    "Cada linha no formato: ingles | traducao em portugues. Numere de 1 a 3, nada mais."
)


def tem_chave() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def _chat(sistema: str, usuario: str) -> str:
    corpo = json.dumps(
        {
            "model": MODELO,
            "messages": [
                {"role": "system", "content": sistema},
                {"role": "user", "content": usuario},
            ],
        }
    ).encode()
    req = urllib.request.Request(
        URL,
        data=corpo,
        headers={
            "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)["choices"][0]["message"]["content"].strip()


def traduzir(texto: str) -> str:
    if not tem_chave():
        return ""
    return _chat(_TRADUZIR, texto)


def sugerir(contexto: str) -> list[tuple[str, str]]:
    if not tem_chave():
        return []
    saida = []
    for linha in _chat(_SUGERIR, contexto).splitlines():
        linha = linha.strip().lstrip("0123456789.) ").strip()
        if not linha:
            continue
        ingles, _, portugues = linha.partition("|")
        saida.append((ingles.strip(), portugues.strip()))
    return saida[:3]
