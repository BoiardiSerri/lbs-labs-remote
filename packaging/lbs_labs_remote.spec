# -*- mode: python ; coding: utf-8 -*-
# PyInstaller: crea dist/LBS Labs Remote (Windows) o "dist/LBS Labs Remote.app" (macOS).
#   python packaging/build_icons.py
#   pyinstaller --noconfirm --clean packaging/lbs_labs_remote.spec
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
ICONS = os.path.join(SPECPATH, "icons")
with open(os.path.join(ROOT, "lbsremote", "__init__.py"), encoding="utf-8") as fh:
    VERSION = re.search(r'__version__ = "([^"]+)"', fh.read()).group(1)

hidden = ["PIL.ImageTk", "tkinter", "tkinter.ttk", "tkinter.messagebox"]
if sys.platform == "darwin":
    hidden += ["pystray._darwin", "pynput.keyboard._darwin", "pynput.mouse._darwin",
               "Quartz", "AppKit", "Foundation", "ApplicationServices", "PyObjCTools.AppHelper"]
    icon = os.path.join(ICONS, "LBSLabsRemote.icns")
elif sys.platform.startswith("win"):
    hidden += ["pystray._win32", "pynput.keyboard._win32", "pynput.mouse._win32"]
    icon = os.path.join(ICONS, "LBSLabsRemote.ico")
else:
    hidden += ["pystray._xorg", "pynput.keyboard._xorg", "pynput.mouse._xorg"]
    icon = None
if icon and not os.path.exists(icon):
    icon = None

a = Analysis(
    [os.path.join(ROOT, "lbs_labs_remote.py")],
    pathex=[ROOT],
    hiddenimports=hidden,
    excludes=["pystray._gtk", "pystray._appindicator", "gi"] if sys.platform != "linux" else [],
    noarchive=False,
)
pyz = PYZ(a.pure)

version_info = None
if sys.platform.startswith("win"):
    # Nome e azienda mostrati in Gestione attività e nelle proprietà del file
    from PyInstaller.utils.win32.versioninfo import (FixedFileInfo, StringFileInfo, StringStruct,
                                                     StringTable, VarFileInfo, VarStruct,
                                                     VSVersionInfo)
    nums = tuple(int(x) for x in (VERSION.split(".") + ["0", "0", "0"])[:4])
    version_info = VSVersionInfo(
        ffi=FixedFileInfo(filevers=nums, prodvers=nums),
        kids=[StringFileInfo([StringTable("041004B0", [
            StringStruct("CompanyName", "LBS Labs"),
            StringStruct("FileDescription", "LBS Labs Remote"),
            StringStruct("ProductName", "LBS Labs Remote"),
            StringStruct("FileVersion", VERSION),
            StringStruct("ProductVersion", VERSION),
            StringStruct("LegalCopyright", "© LBS Labs"),
            StringStruct("OriginalFilename", "LBSLabsRemote.exe")])]),
              VarFileInfo([VarStruct("Translation", [0x0410, 1200])])])
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="LBSLabsRemote",
    console=False,          # nessuna finestra console
    # macOS: LBS_TARGET_ARCH=universal2 crea un'app Universale (Intel + Apple Silicon)
    target_arch=os.environ.get("LBS_TARGET_ARCH") or None,
    icon=icon,
    version=version_info,
)
coll = COLLECT(exe, a.binaries, a.datas, name="LBSLabsRemote")

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="LBS Labs Remote.app",
        icon=icon,
        bundle_identifier="com.lbslabs.remote",
        version=VERSION,
        info_plist={
            "CFBundleName": "LBS Labs Remote",
            "CFBundleDisplayName": "LBS Labs Remote",
            "CFBundleShortVersionString": VERSION,
            "CFBundleVersion": VERSION,
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "11.0",
            "NSHumanReadableCopyright": "© LBS Labs",
        },
    )
