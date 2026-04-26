import base64
import platform
import subprocess
import xml.sax.saxutils as xml_utils

try:
    import pyttsx3
except ImportError:  # pragma: no cover - optional fallback
    pyttsx3 = None

from config.settings import Settings


def _windows_sapi_rate(tts_rate: int) -> int:
    """Convert words-per-minute style rate into Windows SAPI -10..10 scale."""
    return max(-10, min(int((tts_rate - 160) / 14), 10))


def _voice_selection_script(settings: Settings) -> str:
    """Return PowerShell that selects the configured or best available voice."""
    preferred_voice = settings.tts_voice_name or ""
    encoded_preferred = base64.b64encode(preferred_voice.encode("utf-8")).decode("ascii")
    return f"""
$preferredBytes = [Convert]::FromBase64String('{encoded_preferred}')
$preferredVoice = [System.Text.Encoding]::UTF8.GetString($preferredBytes)
$voices = @($speaker.GetInstalledVoices() | ForEach-Object {{ $_.VoiceInfo.Name }})
if ($preferredVoice.Trim().Length -gt 0) {{
    $match = $voices | Where-Object {{ $_ -like "*$preferredVoice*" }} | Select-Object -First 1
    if ($match) {{ $speaker.SelectVoice($match) }}
}} else {{
    $preferredNames = @("Microsoft Zira", "Microsoft Hazel", "Microsoft David")
    foreach ($candidate in $preferredNames) {{
        $match = $voices | Where-Object {{ $_ -like "*$candidate*" }} | Select-Object -First 1
        if ($match) {{
            $speaker.SelectVoice($match)
            break
        }}
    }}
}}
"""


def _speak_with_windows_sapi(text: str, settings: Settings) -> None:
    """Speak text with the built-in Windows speech engine."""
    escaped_text = xml_utils.escape(text)
    ssml = f"""
<speak version="1.0" xml:lang="en-US">
  <prosody rate="-5%" volume="x-loud">{escaped_text}</prosody>
</speak>
"""
    encoded_ssml = base64.b64encode(ssml.encode("utf-8")).decode("ascii")
    rate = _windows_sapi_rate(settings.tts_rate)
    volume = max(0, min(int(settings.tts_volume * 100), 100))
    script = f"""
Add-Type -AssemblyName System.Speech
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
$speaker.Rate = {rate}
$speaker.Volume = {volume}
{_voice_selection_script(settings)}
$bytes = [Convert]::FromBase64String('{encoded_ssml}')
$ssml = [System.Text.Encoding]::UTF8.GetString($bytes)
$speaker.SpeakSsml($ssml)
"""
    encoded_script = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-EncodedCommand",
            encoded_script,
        ],
        check=True,
        creationflags=creation_flags,
        timeout=45,
    )


def _speak_with_pyttsx3(text: str, settings: Settings) -> None:
    """Speak text with pyttsx3 as a cross-platform fallback."""
    if pyttsx3 is None:
        raise RuntimeError("pyttsx3 is not installed.")

    engine = pyttsx3.init()
    engine.setProperty("rate", settings.tts_rate)
    engine.setProperty("volume", settings.tts_volume)
    if settings.tts_voice_name:
        for voice in engine.getProperty("voices"):
            if settings.tts_voice_name.lower() in voice.name.lower():
                engine.setProperty("voice", voice.id)
                break
    engine.say(text)
    engine.runAndWait()


def speak_text(text: str, settings: Settings) -> None:
    """Convert text to speech using the most reliable local engine available."""
    if not text.strip():
        return

    if platform.system().lower() == "windows":
        try:
            _speak_with_windows_sapi(text=text, settings=settings)
            return
        except Exception as error:
            print(f"[warn] Windows SAPI speech failed: {error}")

    _speak_with_pyttsx3(text=text, settings=settings)
