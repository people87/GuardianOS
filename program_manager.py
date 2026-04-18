"""
program_manager.py — GuardianOS Program Manager
Responsabilidade: Listar e desinstalar programas via Winget.
"""
import re
import subprocess
import logging
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm

logger = logging.getLogger("guardianOS")


# ─── Listagem ─────────────────────────────────────────────────────────────────

def _parse_winget_output(stdout: str) -> List[dict]:
    """
    Faz o parsing da saída tabular do Winget usando posição de colunas.
    O Winget usa colunas de largura fixa separadas por espaços — split por espaço
    duplo é frágil para nomes com múltiplos espaços. A linha de hifens (--)
    define a largura exata de cada coluna.

    Args:
        stdout: Saída bruta do comando `winget list`.

    Returns:
        Lista de dicts com 'nome', 'id', 'versao'.
    """
    linhas = stdout.splitlines()

    # Localiza a linha de separador (ex: "---- ---- ----")
    sep_index = next(
        (i for i, l in enumerate(linhas) if re.match(r"^[-]+\s+[-]+", l)),
        None
    )
    if sep_index is None:
        return []

    # Usa o separador para calcular as posições de início de cada coluna
    partes_sep = re.split(r"(\s+)", linhas[sep_index])
    col_starts = [0]
    pos = 0
    for parte in partes_sep:
        pos += len(parte)
        if parte.startswith("-"):
            col_starts.append(pos)

    programas = []
    for linha in linhas[sep_index + 1:]:
        if not linha.strip():
            continue
        try:
            colunas = []
            for i, start in enumerate(col_starts):
                end = col_starts[i + 1] if i + 1 < len(col_starts) else None
                colunas.append(linha[start:end].strip())

            if len(colunas) >= 2 and colunas[0] and colunas[1]:
                programas.append({
                    "nome":   colunas[0],
                    "id":     colunas[1],
                    "versao": colunas[2] if len(colunas) > 2 else "—",
                })
        except IndexError:
            continue

    return programas


def listar_programas_instalados() -> List[dict]:
    """
    Chama o Winget para listar programas instalados e retorna lista estruturada.

    Returns:
        Lista de dicts com 'nome', 'id', 'versao'. Vazia em caso de erro.
    """
    print("\n  🔍 Mapeando programas instalados (Winget)...")
    try:
        resultado = subprocess.run(
            ["winget", "list", "--accept-source-agreements"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        programas = _parse_winget_output(resultado.stdout)
        print(f"  ✅ {len(programas)} programas mapeados.")
        return programas

    except FileNotFoundError:
        print("  ❌ Winget não encontrado. Verifique a instalação do App Installer.")
        return []
    except subprocess.TimeoutExpired:
        print("  ❌ Winget demorou demais para responder (timeout 60s).")
        return []
    except Exception as e:
        print(f"  ❌ Erro inesperado ao listar programas: {e}")
        logger.exception("Erro em listar_programas_instalados")
        return []


# ─── Desinstalação ────────────────────────────────────────────────────────────

def desinstalar_programa(app_id: str, dry_run: bool = False) -> bool:
    """
    Desinstala um programa via Winget.

    Args:
        app_id:  ID exato do app no Winget.
        dry_run: Se True, apenas simula sem desinstalar.

    Returns:
        True se bem-sucedido (ou se dry_run), False caso contrário.
    """
    if dry_run:
        print(f"  📋 [DRY RUN] Seria desinstalado: {app_id}")
        return True

    print(f"  ⚙️  Desinstalando {app_id}...")
    try:
        processo = subprocess.run(
            ["winget", "uninstall", "--id", app_id, "--silent", "--accept-source-agreements"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if processo.returncode == 0:
            print(f"  ✅ {app_id} removido com sucesso!")
            logger.info("DESINSTALADO | %s", app_id)
            return True
        else:
            stderr = processo.stderr.strip()
            print(f"  ⚠️  Falha ao remover {app_id}: {stderr[:100] or 'código ' + str(processo.returncode)}")
            logger.warning("FALHA_DESINSTALAR | %s | %s", app_id, stderr[:100])
            return False

    except subprocess.TimeoutExpired:
        print(f"  ❌ Timeout ao desinstalar {app_id} (>120s)")
        return False
    except Exception as e:
        print(f"  ❌ Erro inesperado: {e}")
        logger.exception("Erro em desinstalar_programa: %s", app_id)
        return False


def desinstalar_em_lote(
    app_ids: List[str],
    dry_run: bool = False,
    max_workers: int = 3,
) -> dict[str, bool]:
    """
    Desinstala múltiplos programas em paralelo (com limite de workers para
    evitar conflitos no Windows Installer).

    Args:
        app_ids:     Lista de IDs a desinstalar.
        dry_run:     Simular sem desinstalar.
        max_workers: Máximo de desinstalações simultâneas (padrão: 3).

    Returns:
        Dict {app_id: sucesso}.
    """
    resultados: dict[str, bool] = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(desinstalar_programa, app_id, dry_run): app_id
            for app_id in app_ids
        }
        with tqdm(total=len(app_ids), desc="  Desinstalando", unit=" app") as pbar:
            for future in as_completed(futures):
                app_id = futures[future]
                try:
                    resultados[app_id] = future.result()
                except Exception as e:
                    resultados[app_id] = False
                    logger.exception("Exceção em lote para %s: %s", app_id, e)
                pbar.update(1)

    return resultados