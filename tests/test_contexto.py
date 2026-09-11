from aside import contexto


def test_sem_pasta_devolve_vazio(tmp_path):
    assert contexto.carregar(tmp_path / "nao-existe") == ""
    assert contexto.nomes(tmp_path / "nao-existe") == []


def test_carrega_md_em_ordem_e_ignora_o_resto(tmp_path):
    (tmp_path / "vaga.md").write_text("Backend role")
    (tmp_path / "perfil.md").write_text("Daniel")
    (tmp_path / "notas.txt").write_text("ignorado")
    texto = contexto.carregar(tmp_path)
    assert texto.index("Daniel") < texto.index("Backend role")
    assert "ignorado" not in texto
    assert contexto.nomes(tmp_path) == ["perfil", "vaga"]


def test_segue_link_simbolico(tmp_path):
    fonte = tmp_path / "fonte.txt"
    fonte.write_text("fonte unica")
    pasta = tmp_path / "ctx"
    pasta.mkdir()
    (pasta / "perfil.md").symlink_to(fonte)
    assert "fonte unica" in contexto.carregar(pasta)
