"""
startup_manager.py — GuardianOS Startup Manager
Responsabilidade: Inventariar, analisar e desabilitar entradas de inicialização do Windows
lendo e escrevendo no Registro com segurança (backup automático antes de qualquer mudança).

Fontes de Startup suportadas:
  - HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run        (usuário, sem admin)
  - HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run        (sistema, requer admin)
  - HKLM\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Run  (apps 32-bit)
  - Pasta Startup do usuário (shell:startup)
  - Pasta Startup do sistema (C:/ProgramData/Microsoft/Windows/Start Menu/Programs/Startup)
"""
import os
import json
import logging
import winreg
import subprocess
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger("guardianOS")

# ─── Chaves de Registro monitoradas ──────────────────────────────────────────

REGISTRY_KEYS: list[tuple[int, str, str]] = [
    # (hive, subkey, etiqueta_legível)
    (
        winreg.HKEY_CURRENT_USER,
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
        "HKCU\\Run (usuário)",
    ),
    (
        winreg.HKEY_LOCAL_MACHINE,
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
        "HKLM\\Run (sistema)",
    ),
    (
        winreg.HKEY_LOCAL_MACHINE,
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run",
        "HKLM\\WOW6432 (32-bit)",
    ),
]

# Pastas de Startup no Explorer
STARTUP_FOLDERS: list[tuple[str, str]] = [
    (os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"), "Startup (usuário)"),
    (r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup",                "Startup (sistema)"),
]

# Processos conhecidos de alto impacto — etiquetas para ajudar o usuário
HIGH_IMPACT_KNOWN: dict[str, str] = {
    "teams":         "⚡ ALTO  | Microsoft Teams",
    "discord":       "⚡ ALTO  | Discord",
    "onedrive":      "⚡ ALTO  | OneDrive",
    "spotify":       "🔸 MÉDIO | Spotify",
    "zoom":          "🔸 MÉDIO | Zoom",
    "skype":         "🔸 MÉDIO | Skype",
    "slack":         "🔸 MÉDIO | Slack",
    "steam":         "🔸 MÉDIO | Steam",
    "epic":          "🔸 MÉDIO | Epic Games Launcher",
    "dropbox":       "🔸 MÉDIO | Dropbox",
    "googledrive":   "🔸 MÉDIO | Google Drive",
    "adobeupdate":   "⚡ ALTO  | Adobe Updater",
    "acrobat":       "🔸 MÉDIO | Adobe Acrobat",
    "cortana":       "🔹 BAIXO | Cortana",
    "securityheal":  "⚡ ALTO  | Security Health Systray",
}


# ─── Modelo de dados ──────────────────────────────────────────────────────────

@dataclass
class StartupEntry:
    """Representa uma entrada de inicialização do Windows."""
    nome:       str
    comando:    str
    fonte:      str            # "registry" | "folder"
    origem:     str            # Label da chave ou pasta
    habilitado: bool = True
    impacto:    str  = "🔹 BAIXO | Desconhecido"
    # Campos de controle interno (não exibidos no menu)
    hive:       Optional[int]  = field(default=None, repr=False)
    subkey:     Optional[str]  = field(default=None, repr=False)
    reg_name:   Optional[str]  = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Classifica o impacto baseado no nome/comando."""
        chave = self.nome.lower().replace(" ", "")
        for token, label in HIGH_IMPACT_KNOWN.items():
            if token in chave or token in self.comando.lower():
                self.impacto = label
                return


# ─── Leitura ──────────────────────────────────────────────────────────────────

def _ler_chave_registro(hive: int, subkey: str, origem: str) -> List[StartupEntry]:
    """
    Lê todas as entradas de uma chave de Registro de startup.

    Args:
        hive:    Constante winreg (ex: winreg.HKEY_CURRENT_USER).
        subkey:  Subcaminho da chave.
        origem:  Etiqueta legível para exibição.

    Returns:
        Lista de StartupEntry encontradas na chave.
    """
    entradas: List[StartupEntry] = []
    try:
        with winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ) as chave:
            i = 0
            while True:
                try:
                    nome, valor, _ = winreg.EnumValue(chave, i)
                    entradas.append(StartupEntry(
                        nome=nome,
                        comando=valor,
                        fonte="registry",
                        origem=origem,
                        hive=hive,
                        subkey=subkey,
                        reg_name=nome,
                    ))
                    i += 1
                except OSError:
                    break  # Fim dos valores da chave
    except PermissionError:
        logger.warning("Permissão negada para ler: %s", subkey)
    except FileNotFoundError:
        pass  # Chave não existe neste sistema — normal
    return entradas


def _ler_pasta_startup(pasta: str, origem: str) -> List[StartupEntry]:
    """
    Lê atalhos (.lnk) e executáveis de uma pasta de Startup.

    Args:
        pasta:  Caminho da pasta.
        origem: Etiqueta legível.

    Returns:
        Lista de StartupEntry encontradas na pasta.
    """
    entradas: List[StartupEntry] = []
    p = Path(pasta)
    if not p.exists():
        return entradas

    for item in p.iterdir():
        if item.suffix.lower() in (".lnk", ".exe", ".bat", ".cmd"):
            entradas.append(StartupEntry(
                nome=item.stem,
                comando=str(item),
                fonte="folder",
                origem=origem,
            ))
    return entradas


def listar_entradas_startup() -> List[StartupEntry]:
    """
    Inventaria todas as entradas de inicialização do sistema.

    Returns:
        Lista consolidada de StartupEntry de todas as fontes.
    """
    print("\n  🔍 Inventariando entradas de inicialização...")
    todas: List[StartupEntry] = []

    for hive, subkey, origem in REGISTRY_KEYS:
        encontradas = _ler_chave_registro(hive, subkey, origem)
        todas.extend(encontradas)
        if encontradas:
            print(f"     {origem}: {len(encontradas)} entrada(s)")

    for pasta, origem in STARTUP_FOLDERS:
        encontradas = _ler_pasta_startup(pasta, origem)
        todas.extend(encontradas)
        if encontradas:
            print(f"     {origem}: {len(encontradas)} atalho(s)")

    # Ordena por impacto (⚡ antes de 🔸 antes de 🔹)
    ordem_impacto = {"⚡": 0, "🔸": 1, "🔹": 2}
    todas.sort(key=lambda e: ordem_impacto.get(e.impacto[0], 9))

    print(f"\n  📊 Total: {len(todas)} entrada(s) de inicialização encontrada(s)")
    return todas


# ─── Backup ───────────────────────────────────────────────────────────────────

def _fazer_backup_registro(entradas: List[StartupEntry], pasta_log: Path) -> Path:
    """
    Salva um snapshot JSON das entradas de startup ANTES de qualquer modificação.
    Permite auditoria e rollback manual.

    Args:
        entradas:  Lista de StartupEntry a registrar.
        pasta_log: Destino do arquivo de backup.

    Returns:
        Caminho do arquivo de backup criado.
    """
    pasta_log.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    arquivo = pasta_log / f"startup_backup_{timestamp}.json"

    snapshot = [
        {k: v for k, v in asdict(e).items() if k not in ("hive",)}
        for e in entradas
    ]
    arquivo.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("BACKUP_STARTUP | %s", arquivo)
    return arquivo


# ─── Desabilitação ────────────────────────────────────────────────────────────

def _desabilitar_entrada_registro(entrada: StartupEntry) -> bool:
    """
    Move a entrada do Registro de `Run` para `Run_Disabled` — convenção
    usada pelo próprio Gerenciador de Tarefas do Windows para desabilitar
    entradas sem deletá-las (reversível).

    Args:
        entrada: StartupEntry com fonte == "registry".

    Returns:
        True se bem-sucedido.
    """
    subkey_disabled = entrada.subkey + r"\AutorunsDisabled"

    try:
        # Lê o valor atual
        with winreg.OpenKey(entrada.hive, entrada.subkey, 0, winreg.KEY_READ) as chave:
            valor, tipo = winreg.QueryValueEx(chave, entrada.reg_name)

        # Cria/abre a chave de desabilitados e escreve lá
        with winreg.CreateKeyEx(entrada.hive, subkey_disabled, 0, winreg.KEY_WRITE) as chave_dis:
            winreg.SetValueEx(chave_dis, entrada.reg_name, 0, tipo, valor)

        # Remove da chave original
        with winreg.OpenKey(entrada.hive, entrada.subkey, 0, winreg.KEY_WRITE) as chave_orig:
            winreg.DeleteValue(chave_orig, entrada.reg_name)

        logger.info("STARTUP_DESABILITADO | REG | %s | %s", entrada.nome, entrada.origem)
        return True

    except PermissionError:
        print(f"\n  ❌ Permissão negada para '{entrada.nome}'. Execute como Administrador.")
        logger.warning("PERM_NEGADA_STARTUP | %s", entrada.nome)
        return False
    except FileNotFoundError:
        print(f"\n  ⚠️  Entrada '{entrada.nome}' não encontrada no Registro (já removida?).")
        return False
    except OSError as e:
        print(f"\n  ❌ OSError ao modificar '{entrada.nome}': {e}")
        logger.error("OSERROR_STARTUP | %s | %s", entrada.nome, e)
        return False


def _desabilitar_entrada_pasta(entrada: StartupEntry) -> bool:
    """
    Renomeia o atalho da pasta Startup adicionando sufixo `.disabled`
    (reversível manualmente).

    Args:
        entrada: StartupEntry com fonte == "folder".

    Returns:
        True se bem-sucedido.
    """
    origem = Path(entrada.comando)
    destino = origem.with_suffix(origem.suffix + ".disabled")

    try:
        origem.rename(destino)
        logger.info("STARTUP_DESABILITADO | FOLDER | %s", entrada.nome)
        return True
    except PermissionError:
        print(f"\n  ❌ Permissão negada para renomear '{entrada.nome}'.")
        return False
    except FileNotFoundError:
        print(f"\n  ⚠️  Arquivo '{entrada.comando}' não encontrado.")
        return False
    except OSError as e:
        print(f"\n  ❌ Erro ao desabilitar '{entrada.nome}': {e}")
        return False


def desabilitar_entradas(
    entradas: List[StartupEntry],
    dry_run: bool = False,
    pasta_log: Path = Path.home() / "GuardianOS_Logs",
) -> dict[str, bool]:
    """
    Desabilita uma lista de entradas de startup com backup automático.

    Args:
        entradas:  Entradas selecionadas para desabilitar.
        dry_run:   Se True, apenas simula.
        pasta_log: Onde salvar o backup JSON.

    Returns:
        Dict {nome_entrada: sucesso}.
    """
    if not entradas:
        print("  ℹ️  Nenhuma entrada selecionada.")
        return {}

    # Backup obrigatório antes de qualquer modificação
    if not dry_run:
        backup_path = _fazer_backup_registro(entradas, pasta_log)
        print(f"\n  💾 Backup salvo em: {backup_path}")

    resultados: dict[str, bool] = {}

    for entrada in entradas:
        if dry_run:
            print(f"  📋 [DRY RUN] Seria desabilitado: {entrada.nome} ({entrada.origem})")
            resultados[entrada.nome] = True
            continue

        if entrada.fonte == "registry":
            resultados[entrada.nome] = _desabilitar_entrada_registro(entrada)
        elif entrada.fonte == "folder":
            resultados[entrada.nome] = _desabilitar_entrada_pasta(entrada)
        else:
            resultados[entrada.nome] = False

        status = "✅" if resultados[entrada.nome] else "❌"
        print(f"  {status} {entrada.nome}")

    sucesso = sum(1 for v in resultados.values() if v)
    print(f"\n  📊 {sucesso}/{len(entradas)} entrada(s) desabilitada(s) com sucesso.")
    if sucesso > 0:
        print("  ℹ️  Reinicie o Windows para que as mudanças tenham efeito.")

    return resultados


# ─── Relatório visual ─────────────────────────────────────────────────────────

def exibir_tabela_startup(entradas: List[StartupEntry]) -> None:
    """
    Exibe tabela formatada das entradas de startup no terminal.

    Args:
        entradas: Lista de StartupEntry a exibir.
    """
    if not entradas:
        print("  ✅ Nenhuma entrada de inicialização encontrada.")
        return

    print(f"\n  {'#':<4} {'NOME':<30} {'IMPACTO':<28} {'ORIGEM'}")
    print(f"  {'─'*4} {'─'*30} {'─'*28} {'─'*22}")

    for i, e in enumerate(entradas, 1):
        nome = e.nome[:28]
        print(f"  {i:<4} {nome:<30} {e.impacto:<28} {e.origem}")