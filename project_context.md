# GuardianOS — Project Context (v2.0)

## 1. Vision & Identity

GuardianOS is a **safe-first, high-performance system optimization platform for Windows**, built with Python and designed for **power users and professionals**.

It prioritizes:
- Transparency over automation
- Safety over aggressiveness
- Observability over blind optimization

GuardianOS is NOT just a cleaner — it is a **diagnostics + optimization + recovery system**.

### Core Philosophy
- Every action must be **traceable, reversible, and explainable**
- No destructive operation without **Dry Run mode**
- Optimization must be **data-driven**, not heuristic-only

---

## 2. Target Positioning

GuardianOS aims to compete conceptually with:
- CCleaner (ease of use, automation)
- BleachBit (transparency, open-source philosophy)

BUT differentiates by:
- Deep diagnostics (memory leaks, error patterns)
- Safer registry handling (risk scoring system)
- Developer-grade observability

---

## 3. Technical Stack (CURRENT — DO NOT CHANGE WITHOUT APPROVAL)

- **Language:** Python 3.12+
- **Environment:** Anaconda
- **OS Target:** Windows 10/11
- **Shell Integration:** PowerShell (Admin Mode)

### Libraries
- `psutil` → system metrics & process inspection
- `winreg` → registry operations
- `subprocess` → system-level commands
- `pathlib` → filesystem abstraction
- `tqdm` → progress visualization
- `questionary` → CLI UX

---

## 4. High-Level Architecture (NEW)

GuardianOS is evolving into a **modular system with clear separation of concerns**:


src/
│
├── core/
│ ├── orchestrator.py # Central execution engine
│ ├── logger.py # Structured logging system
│ ├── safety.py # Dry-run, rollback, permissions
│
├── modules/
│ ├── diagnostics/
│ │ ├── system_scan.py
│ │ ├── memory_analysis.py
│ │ ├── error_pattern_detector.py
│ │
│ ├── optimizer/
│ │ ├── network_optimizer.py
│ │ ├── startup_manager.py
│ │
│ ├── cleaner/
│ │ ├── file_cleaner.py
│ │ ├── registry_cleaner.py
│ │ ├── browser_cleaner.py
│ │
│ ├── program_manager/
│ │ ├── uninstaller.py # REWRITE REQUIRED
│ │ ├── winget_adapter.py
│
├── ui/
│ ├── cli.py
│ ├── prompts.py
│
└── main.py


---

## 5. Core Functional Domains

### 5.1 Diagnostics Engine (CRITICAL PRIORITY)

Must include:
- Real-time system metrics (CPU, RAM, Disk)
- Memory leak detection (background processes)
- Error pattern detection (logs, repeated failures)

### Memory Leak Detection Strategy
- Track RAM usage over time (sampling)
- Detect monotonic growth
- Flag suspicious processes

---

### 5.2 Network Optimization

Must safely implement:
- DNS flush
- Winsock reset
- TCP/IP stack reset (optional)
- Cleanup of inactive sockets

⚠️ All actions must:
- Require admin privileges
- Be logged
- Offer rollback guidance

---

### 5.3 Cleaner System (REWRITE)

Current approach is unsafe and naive.

New approach:
- Rule-based cleaning engine
- Risk scoring (LOW / MEDIUM / HIGH)
- Preview before execution

Targets:
- Temp files
- Logs (.log, .evtx)
- Browser cache
- Orphaned files

---

### 5.4 Registry Cleaner (SAFE MODE FIRST)

- Detect invalid keys (do NOT delete blindly)
- Classify:
  - Broken paths
  - Missing references
- Require confirmation

---

### 5.5 Program Manager (CRITICAL REWRITE)

Current Winget-only approach is insufficient.

New requirements:
- Detect leftover files after uninstall
- Remove registry traces
- Handle broken uninstallers

---

## 6. Safety Layer (MANDATORY)

Every operation must support:

### Dry Run Mode
- Simulate all actions
- Show impact before execution

### Logging
- Structured logs (JSON + human-readable)
- Include:
  - Timestamp
  - Action
  - Result
  - Risk level

### Rollback Strategy
- Backup registry changes
- Track deleted files

---

## 7. Reporting System

Generate:
- Human-readable report
- JSON report (for future integrations)

Include:
- Actions performed
- Issues found
- Performance improvements

---

## 8. UX Guidelines (CLI-FIRST)

- Clear warnings for risky operations
- Color-coded outputs:
  - Green → Safe
  - Yellow → Caution
  - Red → Dangerous
- Progress bars for long operations
- No silent failures

---

## 9. Known Weaknesses (TO FIX)

- Uninstaller is unreliable
- No diagnostics engine
- No rollback system
- No memory leak detection
- Registry cleaning is unsafe

---

## 10. Future Directions

- GUI layer (optional)
- Automation profiles (safe / aggressive)
- Plugin system
- AI-assisted diagnostics

---

## 11. Collaboration & Delivery Protocol (Human + AI)

This project is developed collaboratively between the user and AI engineering assistant.

### 11.1 Language & Documentation Standard
- All code comments and docs written by AI must be in **EN_US**.
- Explanations must prioritize clarity for a beginner-to-intermediate developer.
- Technical terms should be introduced with brief definitions when first used.

### 11.2 Git / GitHub Operations Governance
AI is responsible for assisting with:
- Local git hygiene (`status`, `diff`, branch guidance)
- Commit preparation and message drafting
- Remote sync operations (`push`, `pull`)
- Pull request creation and merge workflow guidance

Safety constraints:
- No commit, push, pull request creation, or merge without explicit user approval.
- No destructive git operations (`reset --hard`, force-push) unless explicitly requested.
- Always summarize planned git actions before execution.

### 11.3 Teaching Mode (Default)
GuardianOS sessions should be educational by default:
- Explain **what** is changing, **why** it is needed, and **how** it works.
- Highlight trade-offs (security, reliability, performance, maintainability).
- Call out known limitations and operational risks before live/destructive actions.

### 11.4 Session Execution Pattern
Each implementation cycle should follow:
1. Analysis and risk identification
2. Small scoped change
3. Verification (lint/tests/manual checks)
4. User review and approval
5. Optional git commit/push/PR actions (only with approval)