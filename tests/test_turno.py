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


def test_podar_corta_em_linha_inteira():
    texto = " ".join(str(n) for n in range(40))
    podado = turno.podar(texto, 20, 2)
    assert turno.linhas(podado, 20) == turno.linhas(texto, 20)[-2:]


def test_corrente_entrega_fechadas_uma_vez_so():
    c = turno.Corrente()
    c.fechar("first sentence.")
    fechadas, parcial = c.pegar()
    assert fechadas == ["first sentence."]
    assert c.pegar() == ([], "")


def test_fechar_limpa_o_parcial_que_virou_frase():
    c = turno.Corrente()
    c.por_parcial("half a sen")
    c.fechar("half a sentence.")
    assert c.pegar() == (["half a sentence."], "")


def test_parcial_sozinho_nao_vira_fechada():
    c = turno.Corrente()
    c.por_parcial("still talking")
    assert c.pegar() == ([], "still talking")


def test_pergunta_fecha_com_menos_silencio():
    assert turno.fechou("Can you hear me?", 0.3, 2.0)
    assert not turno.fechou("I can hear you.", 0.3, 2.0)


def test_turno_fecha_no_silencio_mesmo_sem_texto_novo():
    t = turno.Turno(0.1)
    assert not t.quadro(False, "What is your experience with agents?")
    assert any(t.quadro(True, None) for _ in range(5))


def test_turno_nao_fecha_enquanto_a_pessoa_fala():
    t = turno.Turno(0.1)
    assert not any(t.quadro(False, "and then we") for _ in range(20))
