import subprocess

from aside import nuvem


def test_chave_do_ambiente_vence_o_chaveiro(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-do-ambiente")
    assert nuvem._chave() == "sk-do-ambiente"


def test_chave_do_chaveiro_quando_nao_ha_export(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    nuvem._do_chaveiro.cache_clear()

    class Resposta:
        stdout = "sk-do-chaveiro\n"

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: Resposta())
    assert nuvem._chave() == "sk-do-chaveiro"
    nuvem._do_chaveiro.cache_clear()


def test_sem_secret_tool_fica_sem_chave(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    nuvem._do_chaveiro.cache_clear()

    def ausente(*a, **k):
        raise OSError("secret-tool ausente")

    monkeypatch.setattr(subprocess, "run", ausente)
    assert nuvem._chave() == ""
    nuvem._do_chaveiro.cache_clear()
