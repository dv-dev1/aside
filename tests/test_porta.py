from array import array

from aside import audio

ALTO = array("h", [3000] * audio.QUADRO).tobytes()
MUDO = array("h", [0] * audio.QUADRO).tobytes()


def test_silencio_nao_passa():
    p = audio.Porta()
    assert p.passar(MUDO) == []
    assert not p.falando


def test_primeira_voz_traz_a_prerolagem():
    p = audio.Porta(preroll=2)
    p.passar(MUDO)
    p.passar(MUDO)
    assert p.passar(ALTO) == [MUDO, MUDO, ALTO]


def test_prerolagem_nao_cresce_sem_limite():
    p = audio.Porta(preroll=2)
    for _ in range(50):
        p.passar(MUDO)
    assert len(p.passar(ALTO)) == 3


def test_silencio_no_meio_da_fala_passa():
    p = audio.Porta()
    p.passar(ALTO)
    assert p.passar(MUDO) == [MUDO]


def test_reiniciar_fecha_a_porta():
    p = audio.Porta()
    p.passar(ALTO)
    p.reiniciar()
    assert p.passar(MUDO) == []


def test_reduzir_encolhe_pela_taxa():
    bruto = array("h", [1000] * (audio.QUADRO * audio.FATOR)).tobytes()
    reduzido = array("h")
    reduzido.frombytes(audio.reduzir(bruto))
    assert len(reduzido) == audio.QUADRO
    assert set(reduzido) == {1000}
