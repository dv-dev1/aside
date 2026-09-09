"""A barra: legenda em cima, sugestões embaixo."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, GLib, Gtk  # noqa: E402

SEGUNDOS_ABERTA = 15

CSS = b"""
window, .fundo { background: #FCFCF8; }
.en { font-family: "Schibsted Grotesk", system-ui, sans-serif;
      font-size: 20px; color: #0e0f0c; }
.pt { font-family: "Schibsted Grotesk", system-ui, sans-serif;
      font-size: 15px; color: #6a6c6a; }
.marca { font-family: "Instrument Serif", Georgia, serif; font-size: 13px; color: #6a6c6a; }
.vazio { font-family: "Instrument Serif", Georgia, serif; font-size: 17px; color: #6a6c6a; }
.regua { background: rgba(71, 67, 42, 0.2); min-height: 1px; }
.sug-en { font-family: "Schibsted Grotesk", system-ui, sans-serif;
          font-size: 15px; color: #2F3BAE; }
.sug-pt { font-family: "Schibsted Grotesk", system-ui, sans-serif;
          font-size: 12px; color: #6a6c6a; }
.numero { font-family: "Schibsted Grotesk", system-ui, sans-serif;
          font-size: 12px; color: #5B6BF0; }
.painel { background: rgba(91, 107, 240, 0.06); border-radius: 12px; padding: 10px 14px; }
"""


def _rotulo(classe: str, texto: str = "") -> Gtk.Label:
    r = Gtk.Label(label=texto, xalign=0, wrap=True)
    r.add_css_class(classe)
    return r


class Barra(Adw.Application):
    def __init__(self) -> None:
        super().__init__(application_id="io.github.dvdev1.aside")
        self.connect("activate", self._montar)
        self._fechar_em = None

    def _montar(self, _app) -> None:
        css = Gtk.CssProvider()
        css.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self._en = _rotulo("en")
        self._pt = _rotulo("pt")
        self._vazio = _rotulo("vazio", "esperando alguem falar")

        caixa = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        caixa.set_margin_start(20)
        caixa.set_margin_end(20)
        caixa.set_margin_top(14)
        caixa.set_margin_bottom(14)
        caixa.append(self._vazio)
        caixa.append(self._en)
        caixa.append(self._pt)

        self._sugestoes = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self._sugestoes.add_css_class("painel")
        self._gaveta = Gtk.Revealer(transition_type=Gtk.RevealerTransitionType.SLIDE_UP)
        self._gaveta.set_transition_duration(180)
        self._gaveta.set_child(self._sugestoes)

        regua = Gtk.Box()
        regua.add_css_class("regua")

        raiz = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        raiz.add_css_class("fundo")
        raiz.append(caixa)
        raiz.append(regua)
        raiz.append(self._gaveta)

        self._janela = Gtk.ApplicationWindow(application=self, title="aside")
        self._janela.set_default_size(1100, 130)
        self._janela.set_child(raiz)
        self._janela.present()

    def definir_en(self, texto: str) -> None:
        self._vazio.set_visible(not texto)
        self._en.set_text(texto)

    def definir_pt(self, texto: str) -> None:
        self._pt.set_text(texto)

    def definir_sugestoes(self, itens: list[tuple[str, str]]) -> None:
        while filho := self._sugestoes.get_first_child():
            self._sugestoes.remove(filho)
        for i, (ingles, portugues) in enumerate(itens, 1):
            linha = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            linha.append(_rotulo("numero", str(i)))
            texto = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            texto.append(_rotulo("sug-en", ingles))
            if portugues:
                texto.append(_rotulo("sug-pt", portugues))
            linha.append(texto)
            self._sugestoes.append(linha)
        self._gaveta.set_reveal_child(bool(itens))
        self._reagendar_fechamento()

    def _reagendar_fechamento(self) -> None:
        if self._fechar_em:
            GLib.source_remove(self._fechar_em)
        self._fechar_em = GLib.timeout_add_seconds(SEGUNDOS_ABERTA, self._recolher)

    def _recolher(self) -> bool:
        self._gaveta.set_reveal_child(False)
        self._fechar_em = None
        return False
