# Jarvis PC Voice Assistant (Python)

Production-style, modular local voice assistant with:
- Speech-to-text (`faster-whisper`)
- Offline text-to-speech (`pyttsx3`)
- OpenAI brain fallback
- Command routing (apps, web, system controls)
- Persistent memory
- Optional wake-word mode (`pvporcupine`)

## 1) Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Then edit `.env` and set at least:
- `OPENAI_API_KEY` (for AI responses)
- keep wake-word disabled initially (`WAKE_WORD_ENABLED=false`)

## 2) Run Health Check (Recommended)

```powershell
python -m app.main --doctor
```

This verifies dependencies, microphone availability, and configuration quality.

## 3) Run Assistant

Single-turn mode:

```powershell
python -m app.main --mode once
```

Wake-word loop mode:

```powershell
python -m app.main --mode wake
```

Auto mode (default):

```powershell
python -m app.main
```

Auto mode starts wake-word loop only when wake prerequisites are valid.

## 3.1) Run Without Terminal (Windows EXE)

Build (developer machine):

```powershell
.\.venv\Scripts\Activate.ps1
pyinstaller --noconsole --onefile --name JarvisTray --collect-all pvporcupine --collect-all faster_whisper --collect-all pyttsx3 --hidden-import pystray._win32 --hidden-import PIL.Image app\tray_app.py
```

Run:
- Open `dist\JarvisTray.exe`
- A tray icon appears. Use:
  - **Run once (talk now)**
  - **Exit**

Wake word in tray mode:
- Ensure your `.env` next to the `.exe` has:
  - `WAKE_WORD_ENABLED=true`
  - `PORCUPINE_ACCESS_KEY=<your real key>`

Add to Startup (optional):
- Press `Win + R` → type `shell:startup`
- Create a shortcut to `JarvisTray.exe` in that folder

## 4) Test Suite

```powershell
pytest -q
```

## Docker (dev container)

This lets you code on any PC with Docker installed, without setting up Python locally.

Prereqs:
- Docker Desktop
- Create your env file: copy `.env.example` to `.env` and set keys

Build + run health check:

```powershell
docker compose up --build
```

Run the assistant (single turn):

```powershell
docker compose run --rm jarvis python -m app.main --mode once
```

Run tests:

```powershell
docker compose run --rm jarvis pytest -q
```

Notes:
- Microphone / speaker passthrough from containers can be OS-specific. For pure coding + tests, Docker works great; for live audio I recommend running on the host OS.

## 5) Useful Voice Commands

- `what is the time`
- `search for python async tutorial`
- `open youtube`
- `open notepad`
- `remember that my city is pune`
- `what do you remember about my city`

## 6) Safety Notes

- System control is disabled by default.
- To enable restart/shutdown/lock commands, set:
  - `SYSTEM_CONTROL_ENABLED=true`
- Keep `SYSTEM_SHUTDOWN_DELAY_SECONDS` >= `5`.

## 7) Wake Word Notes

Wake-word mode requires:
- `pvporcupine` installed
- `PORCUPINE_ACCESS_KEY` in `.env`
- `WAKE_WORD_ENABLED=true`
- `WAKE_WORD_PHRASE` set to a supported built-in keyword (default: `jarvis`)
