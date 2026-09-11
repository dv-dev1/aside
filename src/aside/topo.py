"""Faz a janela flutuar acima das outras, via EWMH.

O Mutter no Wayland não implementa `zwlr_layer_shell_v1`, então nenhuma aplicação
Wayland consegue se declarar acima. Sob XWayland o protocolo é o EWMH, e aí ele
obedece — mas só a um ClientMessage enviado à raiz; gravar a propriedade direto ele
descarta. Por isso o app roda com GDK_BACKEND=x11.
"""

import ctypes
from functools import lru_cache

RAIZ_REDIRECT = (1 << 20) | (1 << 19)
CLIENT_MESSAGE = 33
ADICIONAR = 1
FONTE_APLICACAO = 1


class _Evento(ctypes.Structure):
    _fields_ = [
        ("tipo", ctypes.c_int),
        ("serial", ctypes.c_ulong),
        ("enviado", ctypes.c_int),
        ("display", ctypes.c_void_p),
        ("janela", ctypes.c_ulong),
        ("mensagem", ctypes.c_ulong),
        ("formato", ctypes.c_int),
        ("dados", ctypes.c_long * 5),
        ("_uniao", ctypes.c_char * 96),
    ]


# Uma conexão só: abrir uma por chamada vazava conexões com o X a cada
# redimensionamento, e o servidor tem limite de clientes.
@lru_cache(maxsize=1)
def _x11():
    x = ctypes.CDLL("libX11.so.6")
    x.XOpenDisplay.restype = ctypes.c_void_p
    x.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x.XInternAtom.restype = ctypes.c_ulong
    x.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
    x.XDefaultRootWindow.restype = ctypes.c_ulong
    x.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
    x.XSendEvent.argtypes = [
        ctypes.c_void_p,
        ctypes.c_ulong,
        ctypes.c_int,
        ctypes.c_long,
        ctypes.c_void_p,
    ]
    x.XMoveResizeWindow.argtypes = [ctypes.c_void_p, ctypes.c_ulong] + [ctypes.c_int] * 4
    x.XResizeWindow.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_uint, ctypes.c_uint]
    x.XFlush.argtypes = [ctypes.c_void_p]
    return x, x.XOpenDisplay(None)


def flutuar(xid: int) -> bool:
    try:
        x, d = _x11()
    except OSError:
        return False
    if not d:
        return False
    raiz = x.XDefaultRootWindow(d)
    for estado in (b"_NET_WM_STATE_ABOVE", b"_NET_WM_STATE_STICKY", b"_NET_WM_STATE_SKIP_TASKBAR"):
        ev = _Evento()
        ev.tipo = CLIENT_MESSAGE
        ev.enviado = 1
        ev.display = d
        ev.janela = xid
        ev.mensagem = x.XInternAtom(d, b"_NET_WM_STATE", 0)
        ev.formato = 32
        ev.dados[0] = ADICIONAR
        ev.dados[1] = x.XInternAtom(d, estado, 0)
        ev.dados[3] = FONTE_APLICACAO
        x.XSendEvent(d, raiz, 0, RAIZ_REDIRECT, ctypes.byref(ev))
    x.XFlush(d)
    return True


def mover(xid: int, x_px: int, y_px: int, largura: int, altura: int) -> None:
    try:
        x, d = _x11()
    except OSError:
        return
    if d:
        x.XMoveResizeWindow(d, xid, x_px, y_px, largura, altura)
        x.XFlush(d)


def redimensionar(xid: int, largura: int, altura: int) -> None:
    try:
        x, d = _x11()
    except OSError:
        return
    if d:
        x.XResizeWindow(d, xid, largura, altura)
        x.XFlush(d)
