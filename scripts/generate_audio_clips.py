#!/usr/bin/env python3
"""
Generate audio clips for Anti Gravity instant commands.

These clips play instantly with zero TTS generation latency.

Usage:
    python scripts/generate_audio_clips.py

Requires:
    ELEVENLABS_API_KEY environment variable set
"""

import os
import sys
from pathlib import Path

try:
    from elevenlabs import ElevenLabs, Voice, VoiceSettings
except ImportError:
    print("❌ ElevenLabs not installed. Run: pip install elevenlabs")
    sys.exit(1)


# Audio clips to generate
CLIPS = {
    # Volume control
    "volume_up": "Volume up",
    "volume_down": "Volume down",
    "mute": "Muted",
    "unmute": "Unmuted",
    
    # Brightness
    "brightness_up": "Brightness increased",
    "brightness_down": "Brightness decreased",
    
    # Connectivity
    "wifi_on": "WiFi enabled",
    "wifi_off": "WiFi disabled",
    "bluetooth_on": "Bluetooth enabled",
    "bluetooth_off": "Bluetooth disabled",
    
    # Playback
    "pause": "Paused",
    "resume": "Resuming",
    "next": "Next track",
    "previous": "Previous track",
    "skip": "Skipping",
    
    # System
    "screenshot": "Screenshot taken",
    "lock": "Screen locked",
    "sleep": "System sleeping",
    "show_desktop": "Showing desktop",
    
    # General
    "on_it": "On it",
    "got_it": "Got it",
    "done": "Done",
    "ok": "OK",
}


def main():
    """Generate audio clips."""
    # Get API key
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not set")
        print("Set it: export ELEVENLABS_API_KEY=sk_...")
        sys.exit(1)
    
    # Initialize client
    client = ElevenLabs(api_key=api_key)
    
    # Get output directory
    script_dir = Path(__file__).parent
    output_dir = script_dir.parent / "data" / "audio_clips"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🎵 Generating audio clips to: {output_dir}")
    print()
    
    # Generate each clip
    success_count = 0
    for clip_name, text in CLIPS.items():
        try:
            print(f"  Generating: {clip_name:20} → '{text}'...", end=" ")
            
            # Generate audio
            audio = client.text_to_speech.convert(
                voice_id="pNInz6obpgDQGcFmaJgB",  # Adam voice
                text=text,
                model_id="eleven_turbo_v2",     # Lowest latency
            )
            
            # Save to file
            output_path = output_dir / f"{clip_name}.mp3"
            with open(output_path, "wb") as f:
                f.write(audio)
            
            print(f"✓ ({len(audio) // 1024}KB)")
            success_count += 1
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print()
    print(f"✅ Generated {success_count}/{len(CLIPS)} audio clips")
    print(f"📂 Location: {output_dir}")
    print()
    print("💡 Audio clips will now play instantly in Anti Gravity")


if __name__ == "__main__":
    main()
