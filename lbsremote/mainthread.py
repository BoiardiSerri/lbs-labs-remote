"""Esecuzione di codice sul thread principale (necessaria su macOS).

macOS 14 e successivi pretendono che le API della tastiera (Text Services / TIS), usate da pynput
per tradurre i tasti, siano chiamate dal thread principale: da un altro thread il processo termina
all'istante con EXC_BREAKPOINT (dispatch_assert_queue_fail). La sessione di un client gira in un
thread proprio, quindi ogni uso della tastiera di pynput passa da qui.

Sugli altri sistemi le funzioni chiamano direttamente, senza cambiare thread.
"""

from __future__ import annotations

import logging
import sys
import threading

log = logging.getLogger(__name__)

_IS_MAC = sys.platform == "darwin"


def _app_helper():
    try:
        from PyObjCTools import AppHelper  # type: ignore
        return AppHelper
    except ImportError:
        return None


def post_to_main(fn, *args) -> None:
    """Esegue fn(*args) sul thread principale senza aspettare. L'ordine delle chiamate si mantiene."""
    helper = _app_helper() if _IS_MAC else None
    if helper is None or threading.current_thread() is threading.main_thread():
        fn(*args)
        return

    def call():
        try:
            fn(*args)
        except Exception:
            log.exception("operazione sul thread principale fallita")

    helper.callAfter(call)


def run_on_main(fn, *args, timeout: float = 10.0):
    """Esegue fn(*args) sul thread principale e ne restituisce il risultato (o rilancia l'errore)."""
    helper = _app_helper() if _IS_MAC else None
    if helper is None or threading.current_thread() is threading.main_thread():
        return fn(*args)
    done = threading.Event()
    box: dict = {}

    def call():
        try:
            box["result"] = fn(*args)
        except BaseException as exc:  # noqa: BLE001 - viene rilanciata nel thread chiamante
            box["error"] = exc
        finally:
            done.set()

    helper.callAfter(call)
    if not done.wait(timeout):
        raise TimeoutError("il thread principale non risponde")
    if "error" in box:
        raise box["error"]
    return box.get("result")
