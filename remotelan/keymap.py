"""Traduzione degli eventi tastiera di tkinter nel formato del protocollo.

Un tasto viene inoltrato come:
  - {"s": <nome>}  per i tasti speciali (nome = attributo di pynput.keyboard.Key)
  - {"c": <char>}  per i tasti carattere
Nessuna rimappatura Mac/Windows: Cmd arriva come "cmd", Ctrl come "ctrl", ecc.
"""

from __future__ import annotations

# keysym di Tk -> nome di pynput.keyboard.Key
SPECIAL_KEYS = {
    "Shift_L": "shift_l", "Shift_R": "shift_r",
    "Control_L": "ctrl_l", "Control_R": "ctrl_r",
    "Alt_L": "alt_l", "Alt_R": "alt_r",
    "Option_L": "alt_l", "Option_R": "alt_r",        # macOS (Tk recenti)
    "ISO_Level3_Shift": "alt_gr", "Mode_switch": "alt_gr",
    "Meta_L": "cmd_l", "Meta_R": "cmd_r",              # macOS: tasto Command (Tk 8.6)
    "Command": "cmd", "Command_L": "cmd_l", "Command_R": "cmd_r",
    "Super_L": "cmd_l", "Super_R": "cmd_r",
    "Win_L": "cmd_l", "Win_R": "cmd_r",                # Windows: tasto Windows
    "Caps_Lock": "caps_lock",
    "Return": "enter", "KP_Enter": "enter",
    "Tab": "tab", "ISO_Left_Tab": "tab",
    "BackSpace": "backspace",
    "Delete": "delete", "KP_Delete": "delete",
    "Insert": "insert", "KP_Insert": "insert",
    "Home": "home", "KP_Home": "home",
    "End": "end", "KP_End": "end",
    "Prior": "page_up", "KP_Prior": "page_up", "Page_Up": "page_up",
    "Next": "page_down", "KP_Next": "page_down", "Page_Down": "page_down",
    "Up": "up", "KP_Up": "up",
    "Down": "down", "KP_Down": "down",
    "Left": "left", "KP_Left": "left",
    "Right": "right", "KP_Right": "right",
    "space": "space",
    "Menu": "menu", "App": "menu",
    "Num_Lock": "num_lock", "Scroll_Lock": "scroll_lock",
    "Pause": "pause", "Print": "print_screen",
    "XF86AudioPlay": "media_play_pause", "XF86AudioMute": "media_volume_mute",
    "XF86AudioLowerVolume": "media_volume_down", "XF86AudioRaiseVolume": "media_volume_up",
}
SPECIAL_KEYS.update({f"F{i}": f"f{i}" for i in range(1, 21)})

# keysym di Tk -> carattere, usati quando event.char è vuoto o di controllo
# (es. Ctrl+virgola): servono per le scorciatoie con modificatori.
KEYSYM_CHARS = {
    "comma": ",", "period": ".", "minus": "-", "plus": "+", "equal": "=",
    "slash": "/", "backslash": "\\", "semicolon": ";", "colon": ":",
    "apostrophe": "'", "quoteright": "'", "quotedbl": '"', "grave": "`", "quoteleft": "`",
    "bracketleft": "[", "bracketright": "]", "braceleft": "{", "braceright": "}",
    "less": "<", "greater": ">", "exclam": "!", "question": "?", "at": "@",
    "numbersign": "#", "dollar": "$", "percent": "%", "asciicircum": "^",
    "ampersand": "&", "asterisk": "*", "parenleft": "(", "parenright": ")",
    "underscore": "_", "bar": "|", "asciitilde": "~", "section": "§", "degree": "°",
    "sterling": "£", "EuroSign": "€",
    "egrave": "è", "eacute": "é", "agrave": "à", "ograve": "ò", "ugrave": "ù",
    "igrave": "ì", "ccedilla": "ç",
    "KP_Add": "+", "KP_Subtract": "-", "KP_Multiply": "*", "KP_Divide": "/",
    "KP_Decimal": ".", "KP_Separator": ",", "KP_Equal": "=",
}
KEYSYM_CHARS.update({f"KP_{i}": str(i) for i in range(10)})

# Modificatori che trasformano un tasto in "scorciatoia" (non in testo).
SHORTCUT_MODIFIERS = ("ctrl", "alt", "cmd")


def tk_key_to_wire(keysym: str, char: str, modifiers_down: set[str]) -> dict | None:
    """Converte (keysym, char) di un evento Tk in {"s": ..} o {"c": ..}.

    modifiers_down: nomi pynput dei tasti speciali attualmente premuti
    (servono a capire se il tasto fa parte di una scorciatoia).
    Restituisce None per i tasti che non sappiamo inoltrare.
    """
    if keysym in SPECIAL_KEYS:
        return {"s": SPECIAL_KEYS[keysym]}

    shortcut = any(m.startswith(SHORTCUT_MODIFIERS) and m != "alt_gr" for m in modifiers_down)

    if char and len(char) == 1 and char.isprintable():
        # Con Ctrl/Alt/Cmd premuti si inoltra la lettera minuscola: lo Shift
        # eventualmente premuto è già stato inoltrato come tasto a sé, così
        # il PC remoto riceve ad es. Cmd+Shift+z e non un carattere "Z" Unicode.
        if shortcut and char.isascii() and char.isalpha():
            return {"c": char.lower()}
        return {"c": char}

    # char vuoto o di controllo (tipico di Ctrl+lettera): si usa il keysym
    if len(keysym) == 1 and keysym.isprintable():
        return {"c": keysym.lower() if keysym.isascii() and keysym.isalpha() else keysym}
    if keysym in KEYSYM_CHARS:
        return {"c": KEYSYM_CHARS[keysym]}
    return None
