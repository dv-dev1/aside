"""Duas telas na mesma janela: a inicial, e a barra que flutua durante a reunião."""

import json
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")
from gi.repository import Adw, Gdk, GLib, Gtk, WebKit  # noqa: E402

from . import ativos, topo  # noqa: E402

SEGUNDOS_ABERTA = 15
# O CSS quebra a linha com a métrica real da fonte e a caixa mostra só as duas
# últimas. Contar caractere aqui erra a largura e o navegador quebra por cima.
GUARDA_EN = 400
GUARDA_PT = 300
INICIO = (740, 470)
LARGURA = 740
MARGEM = 22
PAINEL = Path(__file__).with_name("painel.html")

# A janela precisa ser transparente para o cartao flutuar com sombra: sem isto o
# Adwaita pinta o fundo do tema e sobra uma moldura escura em volta.
CSS_JANELA = b"window, window.background { background: transparent; box-shadow: none; }"


class Barra(Adw.Application):
    def __init__(self, ao_iniciar=None) -> None:
        super().__init__(application_id="io.github.dvdev1.aside")
        self.connect("activate", self._montar)
        self._ao_iniciar = ao_iniciar
        self._fechar_em = None
        self._pronta = False
        self._na_barra = False
        self._altura = 200
        self._espera: list[str] = []

    def _montar(self, _app) -> None:
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        folha = Gtk.CssProvider()
        folha.load_from_data(CSS_JANELA)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), folha, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        gerente = WebKit.UserContentManager()
        gerente.register_script_message_handler("aside", None)
        gerente.connect("script-message-received::aside", self._recado)

        self._vista = WebKit.WebView(user_content_manager=gerente)
        self._vista.set_background_color(Gdk.RGBA(red=0, green=0, blue=0, alpha=0))
        self._vista.connect("load-changed", self._carregou)
        self._vista.load_html(PAINEL.read_text(), ativos.FONTES.as_uri() + "/")

        self._janela = Adw.ApplicationWindow(application=self, title="aside")
        self._janela.set_default_size(*INICIO)
        self._janela.set_content(self._vista)
        self._janela.present()

    def _carregou(self, _vista, evento) -> None:
        if evento != WebKit.LoadEvent.FINISHED:
            return
        self._pronta = True
        for js in self._espera:
            self._rodar(js)
        self._espera.clear()

    def _recado(self, _gerente, valor) -> None:
        recado = valor.to_string()
        if recado.startswith("altura:"):
            self._altura = int(recado.split(":")[1])
            if self._na_barra:
                GLib.idle_add(self._encaixar)
            return
        if recado != "iniciar":
            return
        self._na_barra = True
        self._rodar("abrirBarra()")
        GLib.timeout_add(160, self._flutuar)
        if self._ao_iniciar:
            self._ao_iniciar()

    def _xid(self) -> int:
        superficie = self._janela.get_surface()
        return getattr(superficie, "get_xid", lambda: 0)()

    def _flutuar(self) -> bool:
        """Só funciona sob XWayland: no Wayland puro nenhuma janela se declara acima."""
        if self._xid():
            topo.flutuar(self._xid())
            self._encaixar()
        return False

    def _encaixar(self) -> bool:
        xid = self._xid()
        if not xid:
            return False
        area = Gdk.Display.get_default().get_monitors()[0].get_geometry()
        topo.mover(xid, area.width - LARGURA - MARGEM, MARGEM, LARGURA, self._altura)
        return False

    def _rodar(self, js: str) -> None:
        if not self._pronta:
            self._espera.append(js)
            return
        self._vista.evaluate_javascript(js, -1, None, None, None, None, None)

    def definir_estado(self, texto: str) -> None:
        self._rodar(f"definirEstado({json.dumps(texto)})")

    def definir_en(self, texto: str) -> None:
        self._rodar(f"definirEn({json.dumps(texto[-GUARDA_EN:])})")

    def definir_pt(self, texto: str) -> None:
        self._rodar(f"definirPt({json.dumps(texto[-GUARDA_PT:])})")

    def definir_sugestoes(self, itens: list[tuple[str, str]]) -> None:
        self._rodar(f"definirSugestoes({json.dumps([list(i) for i in itens])})")
        self._reagendar_fechamento()

    def _reagendar_fechamento(self) -> None:
        if self._fechar_em:
            GLib.source_remove(self._fechar_em)
        self._fechar_em = GLib.timeout_add_seconds(SEGUNDOS_ABERTA, self._recolher)

    def _recolher(self) -> bool:
        self._rodar("definirSugestoes([])")
        self._fechar_em = None
        return False
