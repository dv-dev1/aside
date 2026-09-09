"""Liga captura, transcrição, turno e nuvem na barra."""

import queue
import sys
import threading
from collections import deque

from gi.repository import GLib

from . import ativos, audio, nuvem, turno, ui

SEGUNDOS_POR_QUADRO = audio.QUADRO / audio.TAXA
# ponytail: 300ms por chamada. Medido: 100ms nao adianta a primeira palavra em nada,
# porque os ~1,8s de atraso sao contexto interno do modelo, e custa 3x mais GPU.
QUADROS_POR_CHAMADA = 3
CONTEXTO = 6


def _escutar(barra: ui.Barra, fila: queue.Queue) -> None:
    from .stt import Transcritor

    t = Transcritor()
    silencio = duracao = 0.0
    anterior = ""
    lote: list[float] = []
    porta = audio.Porta()
    try:
        for quadro in audio.quadros():
            passaram = porta.passar(quadro)
            if not passaram:
                continue
            duracao += SEGUNDOS_POR_QUADRO
            silencio = silencio + SEGUNDOS_POR_QUADRO if audio.mudo(quadro) else 0.0
            for q in passaram:
                lote += audio.pcm_float(q)
            if len(lote) < QUADROS_POR_CHAMADA * audio.QUADRO:
                continue
            texto, lote = t.alimentar(lote), []
            if texto != anterior:
                anterior = texto
                GLib.idle_add(barra.definir_en, texto)
            if texto and turno.fechou(texto, silencio, duracao):
                fila.put(t.reiniciar())
                silencio = duracao = 0.0
                anterior = ""
                porta.reiniciar()
    finally:
        t.fechar()


def _pensar(barra: ui.Barra, fila: queue.Queue) -> None:
    historico: deque[str] = deque(maxlen=CONTEXTO)
    while (falado := fila.get()) is not None:
        historico.append(falado)
        try:
            GLib.idle_add(barra.definir_pt, nuvem.traduzir(falado))
            GLib.idle_add(barra.definir_sugestoes, nuvem.sugerir("\n".join(historico)))
        except OSError as e:
            print(f"nuvem indisponivel: {e}", file=sys.stderr)


def main() -> int:
    if not nuvem.tem_chave():
        print(nuvem.SEM_CHAVE, flush=True)
    ativos.fontes()
    ativos.modelo()

    barra = ui.Barra()
    fila: queue.Queue = queue.Queue()
    for alvo in (_escutar, _pensar):
        threading.Thread(target=alvo, args=(barra, fila), daemon=True).start()
    return barra.run([])


if __name__ == "__main__":
    sys.exit(main())
