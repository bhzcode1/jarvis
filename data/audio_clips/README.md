# Anti Gravity Audio Clips

Pre-recorded audio clips for instant command confirmations.

Clips play immediately with zero TTS generation latency.

## Required Clips

Generate these once using ElevenLabs and save as MP3 files:

```
volume_up.mp3         - "Volume up"
volume_down.mp3       - "Volume down"
mute.mp3             - "Muted"
unmute.mp3           - "Unmuted"
brightness_up.mp3    - "Brightness increased"
brightness_down.mp3  - "Brightness decreased"
bluetooth_on.mp3     - "Bluetooth enabled"
bluetooth_off.mp3    - "Bluetooth disabled"
wifi_on.mp3          - "WiFi enabled"
wifi_off.mp3         - "WiFi disabled"
screenshot.mp3       - "Screenshot taken"
lock.mp3             - "Screen locked"
sleep.mp3            - "System sleeping"
pause.mp3            - "Paused"
resume.mp3           - "Resuming"
next.mp3             - "Next track"
previous.mp3         - "Previous track"
on_it.mp3            - "On it"
got_it.mp3           - "Got it"
done.mp3             - "Done"
```

## Generation

Use ElevenLabs API or Web Interface:
1. Go to https://elevenlabs.io
2. Select voice (e.g., "Adam")
3. Generate text-to-speech
4. Download as MP3
5. Place in this directory with correct naming

Or via Python:
```python
from elevenlabs import ElevenLabs

client = ElevenLabs(api_key="YOUR_KEY")

texts = {
    "volume_up.mp3": "Volume up",
    "volume_down.mp3": "Volume down",
    # ... etc
}

for filename, text in texts.items():
    audio = client.text_to_speech.convert(
        voice_id="pNInz6obpgDQGcFmaJgB",  # Adam
        text=text,
        model_id="eleven_turbo_v2",
    )
    with open(filename, 'wb') as f:
        f.write(audio)
```

## Impact

- **Without clips**: ~1-2 second delay for TTS generation
- **With clips**: Instant playback (< 50ms)
- **Total saved**: 1-2 seconds per confirmed command
