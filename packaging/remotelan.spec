# -*- mode: python ; coding: utf-8 -*-
# PyInstaller: crea dist/RemoteLAN (Windows) o dist/RemoteLAN.app (macOS).
#   python packaging/build_icons.py
#   pyinstaller --noconfirm --clean packaging/remotelan.spec
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
ICONS = os.path.join(SPECPATH, "icons")
with open(os.path.join(ROOT, "remotelan", "__init__.py"), encoding="utf-8") as fh:
    VERSION = re.search(r'__version__ = "([^"]+)"', fh.read()).group(1)

hidden = ["PIL.ImageTk", "tkinter", "tkinter.ttk", "tkinter.messagebox"]
if sys.platform == "darwin":
    hidden += ["pystray._darwin", "pynput.keyboard._darwin", "pynput.mouse._darwin",
               "Quartz", "AppKit", "Foundation", "ApplicationServices", "PyObjCTools.AppHelper"]
    icon = os.path.join(ICONS, "RemoteLAN.icns")
elif sys.platform.startswith("win"):
    hidden += ["pystray._win32", "pynput.keyboard._win32", "pynput.mouse._win32"]
    icon = os.path.join(ICONS, "RemoteLAN.ico")
else:
    hidden += ["pystray._xorg", "pynput.keyboard._xorg", "pynput.mouse._xorg"]
    icon = None
if icon and not os.path.exists(icon):
    icon = None

a = Analysis(
    [os.path.join(ROOT, "remotelan_app.py")],
    pathex=[ROOT],
    hiddenimports=hidden,
    excludes=["pystray._gtk", "pystray._appindicator", "gi"] if sys.platform != "linux" else [],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="RemoteLAN",
    console=False,          # nessuna finestra console
    icon=icon,
)
coll = COLLECT(exe, a.binaries, a.datas, name="RemoteLAN")

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="RemoteLAN.app",
        icon=icon,
        bundle_identifier="com.remotelan.app",
        version=VERSION,
        info_plist={
            "CFBundleName": "RemoteLAN",
            "CFBundleDisplayName": "RemoteLAN",
            "CFBundleShortVersionString": VERSION,
            "CFBundleVersion": VERSION,
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "11.0",
            "NSHumanReadableCopyright": "Uso interno in rete locale",
        },
    )
