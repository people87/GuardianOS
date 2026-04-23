import time
import os
import psutil
import scanner
import system_cleaner

def measure_performance(func, *args, **kwargs):
    """Measures execution time and peak memory usage."""
    process = psutil.Process(os.getpid())
    start_mem = process.memory_info().rss / (1024 ** 2)
    start_time = time.perf_counter()
    
    result = func(*args, **kwargs)
    
    end_time = time.perf_counter()
    end_mem = process.memory_info().rss / (1024 ** 2)
    
    print(f"\n--- Results for {func.__name__} ---")
    print(f"Execution Time: {end_time - start_time:.4f} seconds")
    print(f"Memory Usage: {end_mem - start_mem:.2f} MB added")
    return result

def run_audit():
    print("🚀 Starting GuardianOS Performance Audit...")
    
    # Test 1: Scanner Performance on the sandbox
    # We expect high speed due to os.scandir
    measure_performance(scanner.localizar_arquivos_grandes, "./test_sandbox", tamanho_minimo_mb=50)
    
    # Test 2: Cleaner Calculation (Dry Run)
    # Testing if the one-pass I/O logic is efficient
    # Note: Modify system_cleaner temporarily to accept a custom path for testing
    print("\nStarting Cleaner Bench...")
    measure_performance(system_cleaner.limpar_pastas_temporarias, dry_run=True)

if __name__ == "__main__":
    run_audit()