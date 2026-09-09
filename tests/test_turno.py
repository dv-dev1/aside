from aside import turno


def test_ponto_mais_silencio_fecha():
    assert turno.fechou("Sounds good to me.", 0.6, 2.0)


def test_pausa_curta_no_meio_nao_fecha():
    assert not turno.fechou("Sounds good to me.", 0.4, 2.0)


def test_sem_pontuacao_nao_fecha():
    assert not turno.fechou("and then we deploy", 2.0, 3.0)


def test_teto_de_tempo_forca_corte():
    assert turno.fechou("talking without ever stopping", 0.0, turno.TETO_TURNO)


def test_pergunta_tambem_fecha():
    assert turno.fechou("Does that make sense?", 0.6, 2.0)


def test_frases_separa_por_pontuacao():
    assert turno.frases("Hi there. How are you? Fine") == ["Hi there.", "How are you?", "Fine"]
