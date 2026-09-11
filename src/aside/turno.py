"""Quando a outra pessoa terminou de falar."""

import threading

FIM_DE_FRASE = (".", "?", "!")
SILENCIO_FIM = 0.6
SILENCIO_PERGUNTA = 0.3
TETO_TURNO = 15.0


def fechou(texto: str, silencio: float, duracao: float) -> bool:
    """Silêncio sozinho não separa quem terminou de quem está pensando: as duas pausas
    duram uns 400ms. Pontuação do Parakeet é o segundo sinal que desempata."""
    if duracao >= TETO_TURNO:
        return True
    fim = texto.rstrip()
    # Pergunta é onde o candidato mais precisa da sugestão: fecha com menos silêncio.
    if fim.endswith("?"):
        return silencio >= SILENCIO_PERGUNTA
    return fim.endswith(FIM_DE_FRASE) and silencio >= SILENCIO_FIM


def linhas(texto: str, largura: int) -> list[str]:
    saida, atual = [], ""
    for palavra in texto.split():
        if atual and len(atual) + 1 + len(palavra) > largura:
            saida.append(atual)
            atual = palavra
        else:
            atual = f"{atual} {palavra}".strip()
    if atual:
        saida.append(atual)
    return saida


def podar(texto: str, largura: int, guardar: int) -> str:
    """Descarta linhas inteiras do começo: cortar no meio de uma linha mudaria a
    quebra de todas as seguintes."""
    return " ".join(linhas(texto, largura)[-guardar:])


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


class Corrente:
    """Separa o que já fechou do que ainda está em curso. A tradução precisa dessa
    divisão: retraduzir um trecho já lido troca palavras no meio da frase e quem está
    lendo perde o lugar."""

    def __init__(self) -> None:
        self._fechadas: list[str] = []
        self._parcial = ""
        self._trava = threading.Lock()
        self._mudou = threading.Event()

    def por_parcial(self, texto: str) -> None:
        with self._trava:
            self._parcial = texto
        self._mudou.set()

    def fechar(self, texto: str) -> None:
        with self._trava:
            self._fechadas.append(texto)
            self._parcial = ""
        self._mudou.set()

    def esperar(self, limite: float) -> bool:
        mudou = self._mudou.wait(limite)
        self._mudou.clear()
        return mudou

    def pegar(self) -> tuple[list[str], str]:
        with self._trava:
            fechadas, self._fechadas = self._fechadas, []
            return fechadas, self._parcial


class Turno:
    """Avaliado a cada quadro, mesmo quando o texto não muda: é no silêncio depois da
    pergunta que o turno fecha, e nesse silêncio o modelo não produz texto novo."""

    def __init__(self, passo: float) -> None:
        self._passo = passo
        self.reiniciar()

    def reiniciar(self) -> None:
        self.texto = ""
        self.silencio = 0.0
        self.duracao = 0.0

    def quadro(self, mudo: bool, novo: str | None) -> bool:
        self.duracao += self._passo
        self.silencio = self.silencio + self._passo if mudo else 0.0
        if novo is not None:
            self.texto = novo
        return bool(self.texto) and fechou(self.texto, self.silencio, self.duracao)
