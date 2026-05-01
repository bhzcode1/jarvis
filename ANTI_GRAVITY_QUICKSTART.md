# Anti Gravity — Quick Start

Get up and running with speed optimizations in 5 minutes.

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Set API Keys

Create `.env` in the project root:

```env
# Groq (Fast LLM)
GROQ_API_KEY=gsk_xxxxxxxxxxxx

# ElevenLabs (Streaming TTS)
ELEVENLABS_API_KEY=sk_xxxxxxxxxxxx

# (Keep existing keys for fallback)
OPENAI_API_KEY=sk_...
PORCUPINE_ACCESS_KEY=...
```

**Get free API keys:**
- **Groq:** https://console.groq.com (14,400 req/day free)
- **ElevenLabs:** https://elevenlabs.io (10k chars/month free)

## Step 3: Generate Audio Clips (Optional)

For instant command feedback with zero TTS delay:

```bash
python scripts/generate_audio_clips.py
```

This creates MP3 files in `data/audio_clips/` for 30+ common commands.

## Step 4: Run Jarvis

```bash
python main.py
```

Anti Gravity is now active! Try these commands:

**Instant (< 100ms):**
- "volume up"
- "mute"
- "screenshot"
- "lock screen"

**Browser (< 2s):**
- "search amazon for wireless earbuds"
- "open youtube"
- "go to google"

**LLM (< 1s):**
- "tell me a joke"
- "what's the weather"
- "how are you"

---

## Performance

### Before
```
5-10 seconds per command
```

### After Anti Gravity
```
1.2-1.5 seconds for simple commands
2-3 seconds for browser commands
```

---

## Architecture

```
Voice Input
    ↓
Wake Word (instant)
    ↓
STT (faster-whisper < 300ms)
    ↓
Command Router
    ├→ Instant Command? → Local Execution (< 100ms)
    ├→ Browser Command? → Gecko + Groq (< 2s)
    └→ Other? → Groq LLM (< 1s)
    ↓
Response
    ├→ Play Audio Clip (instant) OR
    └→ Stream TTS (< 200ms to first word)
    ↓
Voice Output
```

---

## Modules

### `app/anti_gravity_core.py`
Main AntiGravity class - orchestrates the entire optimization pipeline

### `app/gecko_browser.py`
Browser automation via Selenium/Firefox for voice-controlled web tasks

### `app/instant_commands.py`
50+ local system commands (volume, brightness, WiFi, etc) that execute instantly

### `scripts/generate_audio_clips.py`
Generate pre-recorded confirmation clips for instant feedback

---

## Troubleshooting

### Commands still slow?
- Check that `GROQ_API_KEY` and `ELEVENLABS_API_KEY` are set in `.env`
- Run with debug: `python main.py` (check console output)
- Verify API keys are valid at https://console.groq.com and https://elevenlabs.io

### Audio clips not playing?
- Generate them: `python scripts/generate_audio_clips.py`
- Check `data/audio_clips/` directory exists
- Verify MP3 files are created

### Browser not working?
- Firefox should auto-install via webdriver-manager
- If issues: `pip install --upgrade webdriver-manager`
- Ensure Firefox is installed on your system

### Getting "LLM not configured" errors?
- Set `GROQ_API_KEY` in `.env`
- Restart the app: `python main.py`

---

## Next Steps

1. **Customize system prompt** → Edit in `app/anti_gravity_core.py`
2. **Add instant commands** → Edit `app/instant_commands.py`
3. **Generate audio clips** → `python scripts/generate_audio_clips.py`
4. **Monitor performance** → Check console output for timing info

---

## Documentation

Full documentation: [ANTI_GRAVITY.md](ANTI_GRAVITY.md)

---

## Support

- Issues: GitHub Issues
- Docs: [ANTI_GRAVITY.md](ANTI_GRAVITY.md)
- API Keys: See Step 2 above

---

**Ready to fly? 🚀**
```bash
python main.py
```
