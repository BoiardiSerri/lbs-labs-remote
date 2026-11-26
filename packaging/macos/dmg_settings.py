# Impostazioni di dmgbuild per il DMG di LBS Labs Remote.
# Uso: dmgbuild -s packaging/macos/dmg_settings.py -D app="dist/LBS Labs Remote.app" \
#        -D background=packaging/icons/dmg-background.tiff "LBS Labs Remote" out.dmg
# Le posizioni corrispondono allo sfondo disegnato da packaging/build_icons.py (640×420).
import os.path

application = defines.get("app", "dist/LBS Labs Remote.app")  # noqa: F821 (definito da dmgbuild)
appname = os.path.basename(application)

format = "UDZO"
files = [application]
symlinks = {"Applications": "/Applications"}
background = defines.get("background", "packaging/icons/dmg-background.png")  # noqa: F821
window_rect = ((200, 140), (640, 420))
default_view = "icon-view"
show_status_bar = False
show_tab_view = False
show_toolbar = False
show_pathbar = False
show_sidebar = False
icon_size = 96
text_size = 13
label_pos = "bottom"
icon_locations = {
    appname: (190, 172),
    "Applications": (450, 172),
}
