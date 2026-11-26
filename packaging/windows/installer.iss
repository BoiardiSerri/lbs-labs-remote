; Installer Windows di RemoteLAN (Inno Setup 6).
; Compilazione: ISCC.exe /DAppVersion=1.0.0 packaging\windows\installer.iss
; Prerequisito: pyinstaller packaging\remotelan.spec  (crea dist\RemoteLAN)

#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

[Setup]
AppId={{8F2C1E7A-5B3D-4C9E-9A21-6D7E2F4B1C30}
AppName=RemoteLAN
AppVersion={#AppVersion}
AppVerName=RemoteLAN {#AppVersion}
AppPublisher=RemoteLAN
DefaultDirName={autopf}\RemoteLAN
DefaultGroupName=RemoteLAN
DisableProgramGroupPage=yes
DisableDirPage=yes
OutputDir=Output
OutputBaseFilename=RemoteLAN-Windows-Setup
SetupIconFile=..\icons\RemoteLAN.ico
UninstallDisplayIcon={app}\RemoteLAN.exe
UninstallDisplayName=RemoteLAN
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=force
UsedUserAreasWarning=no

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"

[Tasks]
Name: "autostart"; Description: "Avvia RemoteLAN automaticamente all'accensione (consigliato sul PC da controllare a distanza)"; Flags: unchecked
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\..\dist\RemoteLAN\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\RemoteLAN"; Filename: "{app}\RemoteLAN.exe"
Name: "{autodesktop}\RemoteLAN"; Filename: "{app}\RemoteLAN.exe"; Tasks: desktopicon

[Registry]
; Stesso valore usato dalla voce "Avvia al login" del menu dell'icona
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "RemoteLAN Agent"; ValueData: """{app}\RemoteLAN.exe"" --agent"; Tasks: autostart; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueName: "RemoteLAN Agent"; Flags: dontcreatekey uninsdeletevalue

[Run]
; Regola del firewall: niente richieste di autorizzazione (reti private e di dominio)
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall delete rule name=""RemoteLAN"""; Flags: runhidden; StatusMsg: "Configurazione del firewall..."
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall add rule name=""RemoteLAN"" dir=in action=allow program=""{app}\RemoteLAN.exe"" enable=yes profile=private,domain"; Flags: runhidden; StatusMsg: "Configurazione del firewall..."
Filename: "{app}\RemoteLAN.exe"; Description: "Avvia RemoteLAN adesso"; Flags: nowait postinstall skipifsilent runasoriginaluser

[UninstallRun]
Filename: "{sys}\taskkill.exe"; Parameters: "/F /IM RemoteLAN.exe"; Flags: runhidden; RunOnceId: "KillRemoteLAN"
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall delete rule name=""RemoteLAN"""; Flags: runhidden; RunOnceId: "DelFirewallRule"
