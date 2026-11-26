; Installer Windows di LBS Labs Remote (Inno Setup 6).
; Compilazione: ISCC.exe /DAppVersion=1.0.0 packaging\windows\installer.iss
; Prerequisito: pyinstaller packaging\lbs_labs_remote.spec  (crea dist\LBSLabsRemote)

#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif
; stile della procedura: "modern dark" se questa versione di Inno Setup lo supporta (vedi build.yml)
#ifndef WizStyle
  #define WizStyle "modern"
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
WizardStyle={#WizStyle}
WizardImageFile=..\icons\wizard-large.bmp,..\icons\wizard-large-2x.bmp
WizardSmallImageFile=..\icons\wizard-small.bmp,..\icons\wizard-small-2x.bmp
WizardImageStretch=no
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=force
UsedUserAreasWarning=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Messages]
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nLBS Labs Remote runs in the background and starts automatically with Windows, so this computer can be controlled from other computers on the same network. To control another computer, open LBS Labs Remote from the Start menu.
english.FinishedLabel=LBS Labs Remote is installed and already running in the background (look for the LBS icon near the clock).%n%nTo control another computer, open LBS Labs Remote from the Start menu and type its IP address.

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\..\dist\LBSLabsRemote\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
#ifexist AddBackslash(SourcePath) + "MicrosoftEdgeWebview2Setup.exe"
Source: "MicrosoftEdgeWebview2Setup.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall; Check: NeedsWebView2
#endif

[Icons]
Name: "{autoprograms}\LBS Labs Remote"; Filename: "{app}\LBSLabsRemote.exe"
Name: "{autodesktop}\LBS Labs Remote"; Filename: "{app}\LBSLabsRemote.exe"; Tasks: desktopicon

[Registry]
; Avvio automatico in background (stesso valore della voce "Start at login" del menu dell'icona)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "LBS Labs Remote"; ValueData: """{app}\LBSLabsRemote.exe"" --agent"; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueName: "LBS Labs Remote"; Flags: dontcreatekey uninsdeletevalue

[Run]
; Regola del firewall: niente richieste di autorizzazione (reti private e di dominio)
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall delete rule name=""LBS Labs Remote"""; Flags: runhidden; StatusMsg: "Configuring the firewall..."
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall add rule name=""LBS Labs Remote"" dir=in action=allow program=""{app}\LBSLabsRemote.exe"" enable=yes profile=any"; Flags: runhidden; StatusMsg: "Configuring the firewall..."
#ifexist AddBackslash(SourcePath) + "MicrosoftEdgeWebview2Setup.exe"
Filename: "{tmp}\MicrosoftEdgeWebview2Setup.exe"; Parameters: "/silent /install"; StatusMsg: "Installing Microsoft Edge WebView2..."; Check: NeedsWebView2; Flags: waituntilterminated
#endif
; l'agente parte subito in background, senza chiedere
Filename: "{app}\LBSLabsRemote.exe"; Parameters: "--agent"; Flags: nowait runasoriginaluser
Filename: "{app}\LBSLabsRemote.exe"; Parameters: "--viewer"; Description: "Open LBS Labs Remote to control another computer"; Flags: nowait postinstall skipifsilent runasoriginaluser unchecked

[UninstallRun]
Filename: "{sys}\taskkill.exe"; Parameters: "/F /IM LBSLabsRemote.exe"; Flags: runhidden; RunOnceId: "KillLBSLabsRemote"
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall delete rule name=""LBS Labs Remote"""; Flags: runhidden; RunOnceId: "DelFirewallRule"

[Code]
const
  WebView2Key = 'Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}';

function HasWebView2(Root: Integer; Path: String): Boolean;
var
  Version: String;
begin
  Result := RegQueryStringValue(Root, Path, 'pv', Version) and (Version <> '') and (Version <> '0.0.0.0');
end;

// L'interfaccia usa Microsoft Edge WebView2 (già presente su Windows 11 e su quasi tutti i Windows 10)
function NeedsWebView2: Boolean;
begin
  Result := not (HasWebView2(HKLM, 'SOFTWARE\WOW6432Node\' + WebView2Key) or
                 HasWebView2(HKLM, 'SOFTWARE\' + WebView2Key) or
                 HasWebView2(HKCU, 'Software\' + WebView2Key));
end;
