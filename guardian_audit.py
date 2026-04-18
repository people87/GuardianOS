import os
import time
import psutil
import shutil  # <-- IMPORT ADICIONADO AQUI
from pathlib import Path
import scanner
import system_cleaner

# Configurações do Sandbox
SANDBOX_PATH = Path("./guardian_sandbox")
NUM_FILES = 1000
FILE_SIZE_MB = 60 

def setup_sandbox():
    print(f"🛠️ Criando ambiente de teste: {NUM_FILES} arquivos de {FILE_SIZE_MB}MB...")
    if SANDBOX_PATH.exists():
        shutil.rmtree(SANDBOX_PATH)
    SANDBOX_PATH.mkdir(exist_ok=True)
    
    for i in range(NUM_FILES):
        file_path = SANDBOX_PATH / f"test_file_{i}.tmp"
        # Criando arquivos esparsos (rápidos e leves no disco)
        with open(file_path, "wb") as f:
            f.seek(FILE_SIZE_MB * 1024 * 1024 - 1)
            f.write(b"\0")
    print("✅ Sandbox pronto.\n")

def run_benchmark():
    process = psutil.Process(os.getpid())
    results = []

    # --- TESTE 1: SCANNER ---
    start_time = time.perf_counter()
    mem_before = process.memory_info().rss / (1024**2)
    
    encontrados = scanner.localizar_arquivos_grandes(str(SANDBOX_PATH), tamanho_minimo_mb=50)
    
    scan_time = time.perf_counter() - start_time
    mem_after = process.memory_info().rss / (1024**2)
    results.append(f"SCANNER: {scan_time:.4f}s | Mem: {mem_after - mem_before:.2f}MB | Arqs: {len(encontrados)}")

    # --- TESTE 2: CLEANER (REAL) ---
    start_time = time.perf_counter()
    # Injetamos a pasta sandbox para não apagar arquivos reais do Windows
    liberado = system_cleaner.limpar_pastas_temporarias(dry_run=False, targets=[SANDBOX_PATH])
    
    clean_time = time.perf_counter() - start_time
    results.append(f"CLEANER: {clean_time:.4f}s | Liberado: {liberado / (1024**2):.2f}MB")

    # Exibir Relatório Final
    print("\n" + "="*40)
    print("📊 RELATÓRIO DE PERFORMANCE GUARDIAN OS")
    print("="*40)
    for r in results:
        print(f" - {r}")
    print("="*40)

if __name__ == "__main__":
    setup_sandbox()
    try:
        run_benchmark()
    except Exception as e:
        print(f"❌ Erro durante benchmark: {e}")
    finally:
        if SANDBOX_PATH.exists():
            print("\n🧹 Removendo pasta de sandbox...")
            try:
                shutil.rmtree(SANDBOX_PATH)
            except Exception as e:
                print(f"⚠️ Não foi possível remover a pasta: {e}")