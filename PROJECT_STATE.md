# PROJECT STATE

> The agent must read this file before responding, and update it after every confirmed step. Nothing here changes unless explicitly confirmed by the human.

---

## 1. Project Goal
Build SANI as Aman’s personal AI agent. It should treat Aman as the sole trusted authority, execute his commands, hold natural vocal conversations with interruption/topic switching, eventually understand the screen/video/environment, use internet/research/scraping tools, write and modify code, operate the computer, and require Aman’s confirmation before consequential actions such as pushing code. It should ultimately run 24/7 on a personal server and remain capable of Linux/Raspberry Pi deployment without lowering the architectural standards to fit Raspberry Pi.

## 2. Confirmed Tech Stack
| Component | Tool/Library | Reason for choice | Installed? |
|---|---|---|---|
| Core runtime | Python 3.12 | Primary language for agent, tools, OS integration and backend; cross-platform | Y |
| Project/dependency manager | uv 0.12.4 | Reproducible Python environments, dependency management and lockfile management | Y |
| Agent orchestration | OpenAI Agents SDK | Agent runtime, tools, sessions, guardrails and human approval | Y |
| Model provider | Google Gemini | Current reasoning/model inference provider; Gemini API connection is working | Y |
| Backend/API | FastAPI | API boundary between SANI core and external interfaces | N |
| Validation/schema | Pydantic | Strict typed schemas at tool and API boundaries | Y |
| Browser automation | Playwright | Controlled browser interaction, research and web automation | N |
| Source control | Git 2.55.0.windows.4 | Repository management, diffs, commits, branches and future approval-before-push workflow | Y |
| Remote repository | GitHub | Remote source control and eventual approved push workflow | Account available |
| Initial persistence | SQLite | Lightweight local state/memory without requiring a database server | Y |
| Async runtime | asyncio | Concurrent voice, tools, streaming and interfaces | Built into Python |
| Testing | pytest | Automated testing before allowing SANI to modify/execute project code | Y |
| Authorization | Custom SANI Authority layer | Enforces Aman-controlled permissions independently of LLM instructions | Y |
| Headless Voice Stack | sounddevice, soundfile, miniaudio, edge-tts | Headless in-memory audio capture, decoding, and real-time barge-in interruption | Y |
| Development IDE | Antigravity IDE | User's chosen development environment | Y |
| Environment | Windows 11 | Current development platform | Y |
| Future deployment | Linux / Raspberry Pi | Future deployment target; architecture remains cross-platform | N/A |

## 3. Rejected/Alternative Options
- Docker — NOT selected as a core dependency. It was initially mentioned during environment verification without first establishing it as part of the stack. This was corrected and Docker is not required for the current architecture.
- VS Code as Git editor — NOT selected. Antigravity is the user's primary IDE. Antigravity was checked against available documentation, but its compatibility as Git for Windows' `core.editor` could not be verified. Git installer therefore remained on Vim.
- Manual pip + venv workflow — NOT selected. uv was chosen for project/dependency/environment management.
- GPU/CUDA as a core dependency — NOT selected. The RTX 3050 4 GB GPU is available for optional future local-model acceleration, but SANI's core architecture must not depend on it.
- Local models as a general core dependency — NOT selected. Local models are now selected specifically for the voice layer (Whisper large-v3-turbo (fallback) STT + Kokoro TTS); the broader architecture remains provider-agnostic.
- Raspberry Pi as the development baseline — NOT selected. Raspberry Pi is a future deployment target; architecture will not be weakened to fit its resource constraints.

## 4. Fixed Architecture / Graph
```text
                         ┌───────────────┐
                         │     AMAN      │
                         └───────┬───────┘
                                 │
                    Voice / Text / Discord / UI
                                 │
                         ┌───────▼───────┐
                         │ SANI Interface │
                         └───────┬───────┘
                                 │
                         ┌───────▼───────┐
                         │   SANI CORE    │
                         │ Agent Runtime  │
                         └───────┬───────┘
                                 │
                    ┌────────────▼────────────┐
                    │   AUTHORITY / POLICY   │
                    └────────────┬────────────┘
                                 │
          ┌──────────┬───────────┼───────────┬───────────┐
          ▼          ▼           ▼           ▼           ▼
       Files        Git       Browser       Web       Computer
          │          │           │           │           │
          └──────────┴───────────┴───────────┴───────────┘
                                 │
                              OS / Server
```

Core principle:
```text
Aman
 → Interface
 → SANI Core
 → Authority / Policy
 → Tool
 → OS / External Service
```

The LLM must not receive unrestricted direct control over the operating system. Potentially dangerous operations must pass through SANI's authority/permission layer.

## 5. Step Log
| Step # | Description | Status | Confirmed by human? | Notes |
|---|---|---|---|---|
| 1 | Install Git for Windows | Done | Y | Git 2.55.0.windows.4 verified. Git installer used Vim as default editor because Antigravity Git-editor compatibility could not be verified. |
| 2 | Install uv | Done | Y | uv 0.12.4 installed through WinGet. PATH was temporarily refreshed in the existing Antigravity PowerShell process so the command became available. |
| 3 | Initialize SANI Python project | Done | Y | `uv init --python 3.12` successfully initialized `E:\Projects\SANI`. Generated project files and Git repository are present. |
| 5 | Install pytest and pydantic dependencies | Done | Y | Added pytest and pydantic via `uv add pytest pydantic`. |
| 6 | Build Decision-Only Authority Engine | Done | Y | Implemented `AuthorityEngine` in `sani.authority` producing explicit `AuthorityDecision` objects (`ALLOW`, `DENY`, `POLICY_CONFLICT`, `REQUIRES_CONFIRMATION`) without tool side-effects. |
| 7 | Build Tool Execution Subsystem & Guardrails | Done | Y | Implemented `ToolRunner`, `ToolRegistry`, and filesystem/terminal tools with independent parameter validation. |
| 8 | Build Replaceable Provider Interfaces & SQLite Memory Store | Done | Y | Created `LLMProvider`, `VoiceProvider`, and `MemoryProvider` interfaces, along with `SQLiteMemoryStore` with owner scoping and provenance. |
| 9 | Implement SANI Core Agent Orchestration & Verification Suite | Done | Y | Created `SANIAgent` orchestrator and full test suite (`tests/`). Verified 12/12 tests passing. |
| 10 | Build Non-Authoritative Voice Pipeline | Done | Y | Implemented `AudioRecorder` with silence RMS detection, `GeminiSTTProvider`, `EdgeTTSProvider`, `AudioPlayer`, and `VoicePipeline` (Microphone -> STT -> SANI -> TTS -> Speaker). Voice is strictly informational with zero execution authority. |
| 11 | Select Local Voice Stack | Confirmed | Y | Selected Moonshine for local speech-to-text (STT) and Kokoro for local text-to-speech (TTS), targeting smooth CPU-only laptop operation. |
| 12 | Build Headless Audio, Interruption & Hands-Free Control | Done | Y | Updated STT with Chat API (eliminating AFC warning), added startup mic/voice display, hands-free vocal voice switching, and hands-free microphone switching. |
| 13 | Build Smart Intent Classifier, Pre-Push Audit & Hands-Free GitHub Push | Done | Y | Implemented `SmartIntentClassifier` (`src/sani/voice/intent.py`) categorizing speech into `CHAT`, `CONFIG_VOICE`, `CONFIG_MIC`, `GIT_PUSH`, `PROJECT_AUDIT`, and `EXIT`. Built `GitTool` (`src/sani/tools/git_tool.py`) with automatic `git.exe` resolution, configured Git identity `EzioAman`, created initial commit `6d8ce34`, and set remote `origin` to `https://github.com/EzioAman/SANI.git`. Integrated hands-free vocal audit and GitHub push workflow into `VoicePipeline`. Verified 19/19 unit tests passing. |

## 6. Current State
- Last completed step: Step 13 — Build Smart Intent Classifier, Pre-Push Audit & Hands-Free GitHub Push
- Currently working on: Step 14 — Next capability phase (Screen/Vision context & environment understanding)
- Project directory: `E:\Projects\SANI`
- Current IDE: Antigravity IDE
- Current terminal: Antigravity integrated PowerShell
- Python version: 3.12.7
- uv version: 0.12.4
- Git version: 2.55.0.windows.4
- Remote GitHub Repository: `https://github.com/EzioAman/SANI.git` (branch: `main`)
- Initial Git Commit: `6d8ce34 feat: Baseline SANI Agent Core, Authority Engine, SQLite Store, & Smart Voice Subsystem`
- Dependencies: `openai-agents`, `pytest`, `pydantic`, `google-genai`, `sounddevice`, `soundfile`, `miniaudio`, `numpy`, `edge-tts`, `pyttsx3`
- Authority Engine, Tool Execution Runtime, SQLite Memory Store, Replaceable Interfaces, Headless Voice Engine, Interruption Subsystem, Smart Intent Classifier, Git Tool, and Hands-Free GitHub Push workflow built and verified with 19/19 passing unit test suite
- Blockers: None

## 7. Open Questions
- Which specific Gemini model will be selected/standardized after capability verification?
- Exact Antigravity CLI/editor integration remains unverified.
- Local voice implementation (Whisper large-v3-turbo (fallback) STT + Kokoro TTS) needs to be installed, integrated, and CPU-performance verified.
- Screen/video vision architecture needs to be selected.
- Computer-control implementation needs to be selected.
- Persistent memory architecture beyond initial SQLite needs to be designed.
- Discord interface needs to be implemented later.
- Server hardware/OS for 24/7 deployment needs to be determined later.
- Raspberry Pi model for future deployment has not been selected.

## 8. Verified Facts Log
| Claim | Source | Date checked |
|---|---|---|
| Python 3.12.7 is installed | User-provided PowerShell output | 2026-08-14 |
| Git 2.55.0.windows.4 is installed and available | User-provided PowerShell output | 2026-08-14 |
| uv 0.12.4 is installed and available | User-provided PowerShell output | 2026-08-14 |
| NVIDIA GeForce RTX 3050 has 4096 MiB VRAM | User-provided `nvidia-smi` output | 2026-08-14 |
| SANI project directory is `E:\Projects\SANI` | User confirmation | 2026-08-14 |
| `uv init --python 3.12` successfully initialized the project | User-provided Antigravity screenshot/output | 2026-08-14 |
| uv supports Windows and project/environment/dependency management | Official uv documentation | 2026-08-14 |
| OpenAI Agents SDK supports agents, tools, sessions, guardrails and human-in-the-loop workflows | Official OpenAI Agents SDK documentation | 2026-08-14 |
| FastAPI supports WebSockets | Official FastAPI documentation | 2026-08-14 |
| Playwright provides Python browser automation | Official Playwright documentation | 2026-08-14 |
| Antigravity's documented editor/CLI behavior does not provide verified evidence that its IDE executable can be configured as Git for Windows `core.editor` | Official Antigravity documentation checked during setup | 2026-08-14 |
| Gemini is the current working LLM provider for SANI | User-provided terminal output | 2026-08-14 |
| Local voice stack selected as Whisper large-v3-turbo (fallback) STT + Kokoro TTS | User confirmation | 2026-08-14 |
| Voice execution is deferred to Phase 2; current voice layer remains non-authoritative | User confirmation / project architecture | 2026-08-14 |
