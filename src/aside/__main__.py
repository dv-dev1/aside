"""Liga captura, transcrição, turno e nuvem na barra."""

import os

# A barra só consegue flutuar acima das outras janelas sob XWayland: o Mutter no
# Wayland puro não implementa nenhum protocolo que permita isso. Ver `topo.py`.
os.environ.setdefault("GDK_BACKEND", "x11")

import queue  # noqa: E402
import sys
import threading
from collections import deque

from gi.repository import GLib

from . import ativos, audio, contexto, nuvem, turno, ui

SEGUNDOS_POR_QUADRO = audio.QUADRO / audio.TAXA
QUADROS_POR_CHAMADA = 1
HISTORICO = 6
SEGUNDOS_DE_FOLGA = 2
LARGURA_LINHA = 44
LINHAS_GUARDADAS = 6
ESPERA_TRADUCAO = 0.3
TRADUCOES_SIMULTANEAS = 2


def _traduzir_ao_vivo(barra: "ui.Barra", corrente: turno.Corrente, limpar: threading.Event) -> None:
    """Quem está aprendendo lê português muito mais rápido do que inglês, então é esta
    linha que ele acompanha. Frase fechada traduz uma vez e congela; só a cauda em curso
    é retraduzida, senão o texto se reescreve embaixo de quem está lendo."""
    estado = {"fixo": "", "cauda": "", "pedido": 0, "mostrado": 0}
    trava = threading.Lock()
    vagas = threading.Semaphore(TRADUCOES_SIMULTANEAS)

    def mostrar() -> None:
        texto = f"{estado['fixo']} {estado['cauda']}".strip()
        if texto:
            GLib.idle_add(barra.definir_pt, texto)

    def traduzir_cauda(pedido: int, parcial: str) -> None:
        try:
            traducao = nuvem.traduzir(parcial)
        except OSError as e:
            print(f"traducao indisponivel: {e}", file=sys.stderr)
            return
        finally:
            vagas.release()
        with trava:
            # Duas traduções em voo voltam fora de ordem: a mais velha não pode
            # sobrescrever a mais nova.
            if pedido <= estado["mostrado"]:
                return
            estado["mostrado"] = pedido
            estado["cauda"] = traducao
            mostrar()

    parcial_anterior = ""
    while True:
        corrente.esperar(ESPERA_TRADUCAO)
        if limpar.is_set():
            limpar.clear()
            corrente.pegar()
            with trava:
                estado.update(fixo="", cauda="", mostrado=estado["pedido"])
            parcial_anterior = ""
            continue
        fechadas, parcial = corrente.pegar()
        for frase in fechadas:
            try:
                traducao = nuvem.traduzir(frase)
            except OSError as e:
                print(f"traducao indisponivel: {e}", file=sys.stderr)
                continue
            with trava:
                estado["fixo"] = turno.podar(
                    f"{estado['fixo']} {traducao}", LARGURA_LINHA, LINHAS_GUARDADAS
                )
                estado["cauda"] = ""
                estado["mostrado"] = estado["pedido"]
                mostrar()
            parcial_anterior = ""
        if parcial and parcial != parcial_anterior and vagas.acquire(blocking=False):
            parcial_anterior = parcial
            with trava:
                estado["pedido"] += 1
                pedido = estado["pedido"]
            threading.Thread(target=traduzir_cauda, args=(pedido, parcial), daemon=True).start()


def _capturar(recente: "audio.Recente") -> None:
    for quadro in audio.quadros():
        recente.por(quadro)


def _escutar(
    barra: ui.Barra, fila: queue.Queue, corrente: turno.Corrente, limpar: threading.Event
) -> None:
    from .stt import Transcritor

    t = Transcritor()
    estado = turno.Turno(SEGUNDOS_POR_QUADRO)
    anterior = ""
    fechadas = ""
    lote: list[float] = []
    porta = audio.Porta()
    recente = audio.Recente(int(SEGUNDOS_DE_FOLGA / SEGUNDOS_POR_QUADRO))
    threading.Thread(target=_capturar, args=(recente,), daemon=True).start()
    try:
        while True:
            quadro = recente.pegar()
            if limpar.is_set():
                limpar.clear()
                t.reiniciar()
                porta.reiniciar()
                estado.reiniciar()
                lote, anterior, fechadas = [], "", ""
            if recente.reconheceu_perda():
                t.reiniciar()
                porta.reiniciar()
                estado.reiniciar()
                lote, anterior = [], ""
            passaram = porta.passar(quadro)
            if not passaram:
                continue
            for q in passaram:
                lote += audio.pcm_float(q)
            if len(lote) < QUADROS_POR_CHAMADA * audio.QUADRO:
                continue
            novo, lote = t.alimentar(lote), []
            if novo is not None:
                visivel = f"{fechadas} {novo}".strip()
                if visivel != anterior:
                    anterior = visivel
                    corrente.por_parcial(novo)
                    GLib.idle_add(barra.definir_en, visivel)
            if estado.quadro(audio.mudo(quadro), novo):
                final = t.reiniciar()
                # A legenda não pode voltar ao zero quando o turno fecha: sem guardar o
                # que já foi dito, a tela pisca uma palavra solta e ninguém consegue ler.
                fechadas = turno.podar(f"{fechadas} {final}", LARGURA_LINHA, LINHAS_GUARDADAS)
                corrente.fechar(final)
                fila.put(final)
                estado.reiniciar()
                porta.reiniciar()
    finally:
        t.fechar()


def _pensar(barra: ui.Barra, fila: queue.Queue, reuniao: str, limpar: threading.Event) -> None:
    historico: deque[str] = deque(maxlen=HISTORICO)
    while (falado := fila.get()) is not None:
        if limpar.is_set():
            limpar.clear()
            historico.clear()
        historico.append(falado)
        # Sugestão para uma pergunta que já passou é pior que nenhuma: junta o que
        # chegou enquanto a última chamada rodava e responde só à fala mais recente.
        while not fila.empty():
            historico.append(fila.get_nowait())
        pedido = "\n".join(historico) + f"\n\nResponda a esta ultima fala: {historico[-1]}"
        try:
            GLib.idle_add(barra.definir_sugestoes, nuvem.sugerir(pedido, reuniao))
        except OSError as e:
            print(f"nuvem indisponivel: {e}", file=sys.stderr)


def main() -> int:
    sem_chave = not nuvem.tem_chave()
    if sem_chave:
        print(nuvem.SEM_CHAVE, flush=True)
    ativos.fontes()
    ativos.modelo()

    fila: queue.Queue = queue.Queue()
    corrente = turno.Corrente()
    reuniao = contexto.carregar()
    limpar = {nome: threading.Event() for nome in ("legenda", "traducao", "sugestao")}

    def pedir_limpeza() -> None:
        for sinal in limpar.values():
            sinal.set()

    def comecar() -> None:
        threading.Thread(
            target=_escutar, args=(barra, fila, corrente, limpar["legenda"]), daemon=True
        ).start()
        threading.Thread(
            target=_pensar, args=(barra, fila, reuniao, limpar["sugestao"]), daemon=True
        ).start()
        threading.Thread(
            target=_traduzir_ao_vivo, args=(barra, corrente, limpar["traducao"]), daemon=True
        ).start()

    barra = ui.Barra(ao_iniciar=comecar, ao_limpar=pedir_limpeza)
    if sem_chave:
        barra.definir_estado(nuvem.SEM_CHAVE)
    elif contexto.nomes():
        barra.definir_estado("preparado com: " + ", ".join(contexto.nomes()))
    return barra.run([])


if __name__ == "__main__":
    sys.exit(main())
