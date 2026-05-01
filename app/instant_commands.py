"""
Instant Commands - Local Command Bypass for Zero-Latency Responses

Provides direct system control for common commands without LLM latency.
Matches voice commands and executes locally for sub-100ms response time.
"""

import os
import sys
import subprocess
import pygame
from pathlib import Path


# ───────────────────────────────────────────────────────────────
# SYSTEM CONTROL FUNCTIONS
# ───────────────────────────────────────────────────────────────

def get_volume():
    """Get current system volume (Windows)."""
    try:
        import pycaw
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, 1, None)
        volume = interface.GetMasterVolumeLevelScalar()
        return int(volume * 100)
    except:
        return 50  # Default fallback


def set_volume(level):
    """Set system volume (Windows)."""
    try:
        import pycaw
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        level = max(0, min(100, level))
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, 1, None)
        interface.SetMasterVolumeLevelScalar(level / 100.0, None)
        return True
    except:
        return False


def get_brightness():
    """Get current screen brightness (Windows)."""
    try:
        import screen_brightness_control as sbc
        return sbc.get_brightness()[0]
    except:
        return 50  # Default fallback


def set_brightness(level):
    """Set screen brightness (Windows)."""
    try:
        import screen_brightness_control as sbc
        level = max(10, min(100, level))
        sbc.set_brightness(level)
        return True
    except:
        return False


def toggle_wifi(state):
    """Toggle WiFi on/off (Windows)."""
    try:
        if state.lower() == "on":
            subprocess.run(["netsh", "interface", "set", "interface", "WiFi", "enabled"])
        else:
            subprocess.run(["netsh", "interface", "set", "interface", "WiFi", "disabled"])
        return True
    except:
        return False


def toggle_bluetooth(state):
    """Toggle Bluetooth on/off (Windows via PowerShell)."""
    try:
        ps_cmd = f"(Get-Service bthserv).{'Start' if state.lower() == 'on' else 'Stop'}()"
        subprocess.run(["powershell", "-Command", ps_cmd], shell=False)
        return True
    except:
        return False


def lock_screen():
    """Lock the Windows screen."""
    try:
        subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
        return True
    except:
        return False


def system_sleep():
    """Put system to sleep."""
    try:
        subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0", "1", "0"])
        return True
    except:
        return False


def take_screenshot():
    """Take a screenshot and save to Desktop."""
    try:
        from PIL import ImageGrab
        import time
        desktop = Path.home() / "Desktop"
        filename = desktop / f"screenshot_{int(time.time())}.png"
        img = ImageGrab.grab()
        img.save(filename)
        return str(filename)
    except:
        return None


def minimize_all_windows():
    """Minimize all windows (show desktop)."""
    try:
        subprocess.run(["powershell", "-Command", "(New-Object -ComObject shell.application).MinimizeAll()"])
        return True
    except:
        return False


def open_app(app_name):
    """Open a Windows application by name."""
    try:
        if sys.platform == "win32":
            os.startfile(app_name)
            return True
    except:
        return False


# ───────────────────────────────────────────────────────────────
# AUDIO CLIP PLAYBACK
# ───────────────────────────────────────────────────────────────

def get_audio_clips_dir():
    """Get the audio clips directory path."""
    app_dir = Path(__file__).parent.parent
    return app_dir / "data" / "audio_clips"


def play_audio_clip(clip_name):
    """Play a pre-recorded audio clip."""
    clips_dir = get_audio_clips_dir()
    clip_path = clips_dir / f"{clip_name}.mp3"
    
    if not clip_path.exists():
        return False
    
    try:
        pygame.mixer.music.load(str(clip_path))
        pygame.mixer.music.play()
        return True
    except:
        return False


# ───────────────────────────────────────────────────────────────
# INSTANT COMMAND REGISTRY
# ───────────────────────────────────────────────────────────────

def create_instant_commands_dict():
    """Create the instant commands dictionary with all local actions."""
    return {
        # Volume control
        "volume up": lambda: set_volume(get_volume() + 10),
        "turn volume up": lambda: set_volume(get_volume() + 10),
        "increase volume": lambda: set_volume(get_volume() + 10),
        
        "volume down": lambda: set_volume(get_volume() - 10),
        "turn volume down": lambda: set_volume(get_volume() - 10),
        "decrease volume": lambda: set_volume(get_volume() - 10),
        
        "mute": lambda: set_volume(0),
        "unmute": lambda: set_volume(50),
        
        # Brightness control
        "brightness up": lambda: set_brightness(get_brightness() + 10),
        "turn brightness up": lambda: set_brightness(get_brightness() + 10),
        "increase brightness": lambda: set_brightness(get_brightness() + 10),
        
        "brightness down": lambda: set_brightness(get_brightness() - 10),
        "turn brightness down": lambda: set_brightness(get_brightness() - 10),
        "decrease brightness": lambda: set_brightness(get_brightness() - 10),
        
        # Connectivity
        "wifi on": lambda: toggle_wifi("on"),
        "turn wifi on": lambda: toggle_wifi("on"),
        "enable wifi": lambda: toggle_wifi("on"),
        
        "wifi off": lambda: toggle_wifi("off"),
        "turn wifi off": lambda: toggle_wifi("off"),
        "disable wifi": lambda: toggle_wifi("off"),
        
        "bluetooth on": lambda: toggle_bluetooth("on"),
        "turn bluetooth on": lambda: toggle_bluetooth("on"),
        "enable bluetooth": lambda: toggle_bluetooth("on"),
        
        "bluetooth off": lambda: toggle_bluetooth("off"),
        "turn bluetooth off": lambda: toggle_bluetooth("off"),
        "disable bluetooth": lambda: toggle_bluetooth("off"),
        
        # System control
        "screenshot": lambda: take_screenshot(),
        "take a screenshot": lambda: take_screenshot(),
        "take screenshot": lambda: take_screenshot(),
        
        "lock": lambda: lock_screen(),
        "lock screen": lambda: lock_screen(),
        "lock the computer": lambda: lock_screen(),
        
        "sleep": lambda: system_sleep(),
        "go to sleep": lambda: system_sleep(),
        "put the computer to sleep": lambda: system_sleep(),
        
        "show desktop": lambda: minimize_all_windows(),
        "minimize all": lambda: minimize_all_windows(),
        "minimize everything": lambda: minimize_all_windows(),
    }


# ───────────────────────────────────────────────────────────────
# COMMAND MATCHING & EXECUTION
# ───────────────────────────────────────────────────────────────

INSTANT_COMMANDS = create_instant_commands_dict()


def is_instant_command(text: str) -> bool:
    """Check if a command is in the instant commands registry."""
    text_lower = text.lower().strip()
    for keyword in INSTANT_COMMANDS.keys():
        if keyword in text_lower:
            return True
    return False


def execute_instant_command(text: str) -> tuple[bool, str]:
    """
    Execute an instant command if matched.
    
    Args:
        text: User command text
    
    Returns:
        tuple: (success: bool, response_text: str)
    """
    text_lower = text.lower().strip()
    
    for keyword, action in INSTANT_COMMANDS.items():
        if keyword in text_lower:
            try:
                result = action()
                
                # Play audio clip if available
                clip_name = keyword.replace(" ", "_")
                play_audio_clip(clip_name)
                
                return (True, keyword)
            except Exception as e:
                return (False, f"Error executing {keyword}: {str(e)}")
    
    return (False, "")


# ───────────────────────────────────────────────────────────────
# BROWSER COMMAND DETECTION
# ───────────────────────────────────────────────────────────────

BROWSER_KEYWORDS = [
    "search",
    "open",
    "go to",
    "find on",
    "look up",
    "browse",
    "website",
    "google",
    "youtube",
    "amazon",
    "download from",
    "visit",
    "navigate to",
    "check",
    "read",
    "show me",
]


def needs_browser(text: str) -> bool:
    """Check if a command requires browser automation."""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in BROWSER_KEYWORDS)


def needs_llm(text: str) -> bool:
    """Check if a command needs LLM processing (not instant, not browser)."""
    return not is_instant_command(text) and not needs_browser(text)
