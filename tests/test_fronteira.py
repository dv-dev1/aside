"""O README promete que o áudio nunca sai da máquina. Este teste é o que prende a frase."""

import ast
from pathlib import Path

FONTE = Path(__file__).resolve().parents[1] / "src" / "aside"
TOCAM_AUDIO = ("audio.py", "stt.py")
REDE = {"urllib", "http", "socket", "requests", "httpx", "ftplib", "smtplib"}


def _importados(caminho: Path) -> set[str]:
    arvore = ast.parse(caminho.read_text())
    nomes = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            nomes.update(a.name.split(".")[0] for a in no.names)
        elif isinstance(no, ast.ImportFrom) and no.module and no.level == 0:
            nomes.add(no.module.split(".")[0])
    return nomes


def test_modulos_de_audio_nao_abrem_rede():
    for nome in TOCAM_AUDIO:
        vazando = _importados(FONTE / nome) & REDE
        assert not vazando, f"{nome} importa {vazando} e ele carrega PCM"


def test_so_nuvem_fala_com_a_openai():
    culpados = [p.name for p in FONTE.glob("*.py") if "api.openai.com" in p.read_text()]
    assert culpados == ["nuvem.py"], culpados
