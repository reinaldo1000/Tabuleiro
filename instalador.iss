#define MeuProgramaNome "Tabuleiro"
#define MeuProgramaVersao "1.1.0"
#define MeuProgramaEmpresa "Reinaldo"
#define MeuProgramaExe "Tabuleiro.exe"

[Setup]
AppId={{A5957F67-A1E8-4E53-8B72-A2AC147BF885}
AppName={#MeuProgramaNome}
AppVersion={#MeuProgramaVersao}
AppPublisher={#MeuProgramaEmpresa}

DefaultDirName={autopf}\{#MeuProgramaNome}
DefaultGroupName={#MeuProgramaNome}

OutputDir=instalador
OutputBaseFilename=Instalador-Tabuleiro-{#MeuProgramaVersao}

Compression=lzma2
SolidCompression=yes

WizardStyle=modern
PrivilegesRequired=lowest

UninstallDisplayName={#MeuProgramaNome}
UninstallDisplayIcon={app}\{#MeuProgramaExe}

ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos:"; Flags: unchecked

[Files]
Source: "dist\{#MeuProgramaExe}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MeuProgramaNome}"; Filename: "{app}\{#MeuProgramaExe}"
Name: "{autodesktop}\{#MeuProgramaNome}"; Filename: "{app}\{#MeuProgramaExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MeuProgramaExe}"; Description: "Executar {#MeuProgramaNome}"; Flags: nowait postinstall skipifsilent