import os
from pathlib import Path

def create_stress_environment(base_path="./test_sandbox", num_folders=10, files_per_folder=100):
    """Creates a fake directory tree with large files."""
    base = Path(base_path)
    base.mkdir(exist_ok=True)
    
    print(f"Creating {num_folders * files_per_folder} files...")
    for i in range(num_folders):
        sub = base / f"folder_{i}"
        sub.mkdir(exist_ok=True)
        for j in range(files_per_folder):
            f = sub / f"file_{j}.tmp"
            # Create a 60MB file (above our 50MB threshold)
            with open(f, "wb") as dummy:
                dummy.seek(60 * 1024 * 1024 - 1)
                dummy.write(b"\0")
    print("Done. Environment ready.")

if __name__ == "__main__":
    create_stress_environment()