"""Tradução e sugestão de resposta. Único módulo que abre rede."""

import argparse
import json
import os
import sys
import urllib.request

from . import contexto

MODELO = "gpt-4o-mini"
URL = "https://api.openai.com/v1/chat/completions"
SEM_CHAVE = "OPENAI_API_KEY nao definida — legenda em ingles continua, traducao off"

_TRADUZIR = "Traduza para portugues do Brasil. Responda so com a traducao, nada mais."
_FORMATO = (
    "Cada linha no formato: resposta em ingles | traducao em portugues. Numere de 1 a 3, nada mais."
)
_SUGERIR = (
    "Voce ajuda alguem com ingles limitado numa reuniao. A partir do que a outra pessoa "
    "falou, escreva 3 respostas curtas em ingles simples, ate 12 palavras, com palavras comuns. "
    + _FORMATO
)
_ENTREVISTA = (
    "Voce e o ponto eletronico de um candidato numa entrevista de emprego em ingles. Ele "
    "NAO quer parecer fluente: quer so que o outro entenda o que ele diz e perceba que ele "
    "entende tambem. Escreva ingles correto e simples, de quem esta aprendendo bem: frases "
    "curtas e diretas, no maximo 15 palavras, palavras comuns do dia a dia, sem expressao "
    "idiomatica, sem vocabulario sofisticado, sem frase com varias oracoes. Sempre em "
    "primeira pessoa.\n"
    "Use SO os fatos do contexto acima. Nunca invente empregos, numeros, clientes, datas, "
    "ferramentas ou experiencias. Obedeca toda restricao escrita no perfil, principalmente "
    "as de NDA e as de como descrever metricas. Nao contradiga o curriculo enviado nem o "
    "que ja foi dito por escrito ao recrutador.\n"
    "Quando o perfil tiver numero concreto para o que ele esta contando (antes e depois, "
    "porcentagem, custo), use o numero: e o que torna a resposta crivel. Prefira respostas "
    "que liguem uma experiencia real dele ao que a vaga pede.\n"
    "Se a ultima fala foi uma pergunta, as 3 opcoes respondem direto a ela. "
    "Se nao foi pergunta, escreva 3 respostas curtas e naturais para manter a conversa.\n"
    + _FORMATO
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


def _sistema(reuniao: str) -> str:
    if not reuniao:
        return _SUGERIR
    # O contexto vem antes das instruções porque não muda entre chamadas: a OpenAI
    # reaproveita prefixo idêntico em cache, o que corta latência de cada sugestão.
    return f"{reuniao}\n\n---\n\n{_ENTREVISTA}"


def sugerir(fala: str, reuniao: str = "") -> list[tuple[str, str]]:
    if not tem_chave():
        return []
    saida = []
    for linha in _chat(_sistema(reuniao), fala).splitlines():
        linha = linha.strip().lstrip("0123456789.) ").strip()
        if not linha:
            continue
        ingles, _, portugues = linha.partition("|")
        saida.append((ingles.strip(), portugues.strip()))
    return saida[:3]


def main() -> int:
    ap = argparse.ArgumentParser(prog="aside.nuvem")
    ap.add_argument("--pergunta", required=True)
    args = ap.parse_args()
    if not tem_chave():
        print(SEM_CHAVE)
        return 1
    for ingles, portugues in sugerir(args.pergunta, contexto.carregar()):
        print(f"- {ingles}\n  {portugues}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
