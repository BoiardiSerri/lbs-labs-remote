; Installer Windows di LBS Labs Remote (Inno Setup 6).
; Compilazione: ISCC.exe /DAppVersion=1.0.0 packaging\windows\installer.iss
; Prerequisito: pyinstaller packaging\lbs_labs_remote.spec  (crea dist\LBSLabsRemote)

#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

[Setup]
AppId={{29F091FA-FB71-4653-B29A-107ABB0F525F}
AppName=LBS Labs Remote
AppVersion={#AppVersion}
AppVerName=LBS Labs Remote {#AppVersion}
AppPublisher=LBS Labs
DefaultDirName={autopf}\LBS Labs Remote
DefaultGroupName=LBS Labs Remote
DisableProgramGroupPage=yes
DisableDirPage=yes
OutputDir=Output
OutputBaseFilename=LBS-Labs-Remote-Windows-Setup
SetupIconFile=..\icons\LBSLabsRemote.ico
UninstallDisplayIcon={app}\LBSLabsRemote.exe
UninstallDisplayName=LBS Labs Remote
VersionInfoCompany=LBS Labs
VersionInfoProductName=LBS Labs Remote
AppCopyright=© LBS Labs
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=force
UsedUserAreasWarning=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "autostart"; Description: "Start LBS Labs Remote automatically when Windows starts (recommended on the computer to be controlled remotely)"; Flags: unchecked
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\..\dist\LBSLabsRemote\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\LBS Labs Remote"; Filename: "{app}\LBSLabsRemote.exe"
Name: "{autodesktop}\LBS Labs Remote"; Filename: "{app}\LBSLabsRemote.exe"; Tasks: desktopicon

[Registry]
; Stesso valore usato dalla voce "Avvia al login" del menu dell'icona
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "LBS Labs Remote"; ValueData: """{app}\LBSLabsRemote.exe"" --agent"; Tasks: autostart; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueName: "LBS Labs Remote"; Flags: dontcreatekey uninsdeletevalue

[Run]
; Regola del firewall: niente richieste di autorizzazione (reti private e di dominio)
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall delete rule name=""LBS Labs Remote"""; Flags: runhidden; StatusMsg: "Configuring the firewall..."
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall add rule name=""LBS Labs Remote"" dir=in action=allow program=""{app}\LBSLabsRemote.exe"" enable=yes profile=private,domain"; Flags: runhidden; StatusMsg: "Configuring the firewall..."
Filename: "{app}\LBSLabsRemote.exe"; Description: "Launch LBS Labs Remote now"; Flags: nowait postinstall skipifsilent runasoriginaluser

[UninstallRun]
Filename: "{sys}\taskkill.exe"; Parameters: "/F /IM LBSLabsRemote.exe"; Flags: runhidden; RunOnceId: "KillLBSLabsRemote"
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall delete rule name=""LBS Labs Remote"""; Flags: runhidden; RunOnceId: "DelFirewallRule"
