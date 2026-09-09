"""Quando a outra pessoa terminou de falar."""

FIM_DE_FRASE = (".", "?", "!")
SILENCIO_FIM = 0.6
TETO_TURNO = 15.0


def fechou(texto: str, silencio: float, duracao: float) -> bool:
    """Silêncio sozinho não separa quem terminou de quem está pensando: as duas pausas
    duram uns 400ms. Pontuação do Parakeet é o segundo sinal que desempata."""
    if duracao >= TETO_TURNO:
        return True
    return texto.rstrip().endswith(FIM_DE_FRASE) and silencio >= SILENCIO_FIM


def frases(texto: str) -> list[str]:
    saida, atual = [], ""
    for ch in texto:
        atual += ch
        if ch in FIM_DE_FRASE:
            saida.append(atual.strip())
            atual = ""
    if atual.strip():
        saida.append(atual.strip())
    return saida
