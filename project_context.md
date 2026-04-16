# 🛡️ GuardianOS: Project Context & State

## 1. Vision & Identity
GuardianOS is a professional-grade system optimizer and cleaner for Windows, built with Python. 
It targets power users who need transparency and control over system resources.
- **Lead Dev:** User (Programmer & Lawyer)
- **Design Philosophy:** Command-line first, zero-bloat, high-visibility (tqdm/questionary).

## 2. Technical Stack
- **Language:** Python 3.12+ (Anaconda environment)
- **Shell:** Windows PowerShell (Admin Mode)
- **UI:** Questionary (Interactive CLI)
- **Logic:** Pathlib (Filesystem), Subprocess (System commands), tqdm (Progress bars).
- **Package Manager:** Winget integration.

## 3. Current Architecture (MVP)
- `main.py`: Main entry point and interactive menu.
- `scanner.py`: Recursive file mapping and large file identification (>50MB).
- `system_cleaner.py`: Logic for Temp/Prefetch cleanup and Appx (Bloatware) removal.
- `program_manager.py`: Winget-based uninstaller and program listing.

## 4. Work Done So Far
- [x] Initialized Git repository and connected to GitHub.
- [x] Cleaned ~10GB of Outlook cache (.ost).
- [x] Implemented logic to kill Adobe "vampire" processes.
- [x] Built interactive checkbox UI for file deletion.
- [x] Integrated Winget for program management.

## 5. Next Milestones (Roadmap)
- [ ] **Startup Manager:** List and disable high-impact startup apps.
- [ ] **Browser Cleanup:** Cache and cookie removal for Chrome/Edge.
- [ ] **Log Rotation:** Cleanup of Windows `.log` and `.evtx` files.
- [ ] **Dashboard:** Real-time system stats (CPU/RAM/Disk usage) before/after cleaning.