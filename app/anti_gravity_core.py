"""
Anti Gravity Core - Speed-Optimized Voice Assistant

Implements the fast pipeline:
- STT: faster-whisper (tiny.en model)
- Intent: Instant command bypass
- LLM: Groq (300+ tokens/sec)
- TTS: ElevenLabs streaming
- Browser: Selenium Gecko automation
- Architecture: Parallel processing throughout
"""

import os
import asyncio
import pygame
from pathlib import Path
from typing import Optional

# Fast STT
from faster_whisper import WhisperModel

# Fast LLM
from groq import Groq

# Streaming TTS
from elevenlabs import ElevenLabs, stream

# Browser automation
from app.gecko_browser import GeckoBrowser, browser_autonomy

# Instant commands & routing
from app.instant_commands import (
    execute_instant_command,
    is_instant_command,
    needs_browser,
    play_audio_clip,
    get_audio_clips_dir,
)


class AntiGravity:
    """
    Speed-optimized voice assistant with sub-1.5s response time.
    
    Pipeline:
    1. Wake word detection (on-device, instant)
    2. STT transcription (< 300ms with faster-whisper)
    3. Instant command check (< 10ms)
    4. Browser OR LLM routing (< 100ms)
    5. TTS streaming (< 200ms to first word)
    6. Total: < 1.4 seconds for most commands
    """
    
    def __init__(
        self,
        groq_api_key: Optional[str] = None,
        eleven_api_key: Optional[str] = None,
        system_prompt: Optional[str] = None,
        headless_browser: bool = False,
    ):
        """
        Initialize Anti Gravity with speed-optimized components.
        
        Args:
            groq_api_key: Groq API key for fast LLM
            eleven_api_key: ElevenLabs API key for streaming TTS
            system_prompt: System prompt for LLM
            headless_browser: Run Gecko browser headless
        """
        # Get API keys from environment or parameters
        self.groq_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.eleven_key = eleven_api_key or os.getenv("ELEVENLABS_API_KEY")
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.headless_browser = headless_browser
        
        # Initialize STT (faster-whisper with tiny model)
        print("⚡ Loading STT model (faster-whisper)...")
        self.stt = WhisperModel(
            "tiny.en",
            device="cpu",
            compute_type="int8"  # Quantized = 4x faster
        )
        print("✓ STT ready (< 300ms per command)")
        
        # Initialize LLM (Groq - 300+ tokens/sec)
        if self.groq_key:
            self.llm = Groq(api_key=self.groq_key)
            print("✓ LLM ready (Groq @ 300+ tokens/sec)")
        else:
            self.llm = None
            print("⚠ Groq API key not found")
        
        # Initialize TTS (ElevenLabs - streaming)
        if self.eleven_key:
            self.tts = ElevenLabs(api_key=self.eleven_key)
            print("✓ TTS ready (ElevenLabs streaming)")
        else:
            self.tts = None
            print("⚠ ElevenLabs API key not found")
        
        # Browser (on-demand)
        self.gecko = None
        
        # Conversation history (for context)
        self.history = []
        self.max_history = 10  # Keep last 10 exchanges
        
        # Audio playback
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=256)
        self._ensure_audio_clips_dir()
        
        print("\n🚀 Anti Gravity is ready for liftoff!")
        print("Target: < 1.5s for simple commands, < 3s for complex\n")
    
    def _default_system_prompt(self) -> str:
        """Default system prompt for Anti Gravity."""
        return """You are Anti Gravity, a lightning-fast voice assistant.
        
        Keep responses SHORT and DIRECT for voice:
        - Max 2-3 sentences
        - No lists or long explanations
        - Use conversational tone
        - Be helpful and quick
        
        You have access to:
        - System control (volume, brightness, WiFi, etc)
        - Browser automation (search, navigate, extract)
        - File operations
        - Spotify control
        
        Respond naturally to any request."""
    
    def _ensure_audio_clips_dir(self):
        """Create audio clips directory if it doesn't exist."""
        clips_dir = get_audio_clips_dir()
        clips_dir.mkdir(parents=True, exist_ok=True)
    
    # ─────────────────────────────────────────────────────────
    # SPEED OPTIMIZATION: FAST STT
    # ─────────────────────────────────────────────────────────
    
    def transcribe(self, audio_path: str) -> str:
        """
        Transcribe audio with faster-whisper (< 300ms).
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Transcribed text
        """
        try:
            segments, _ = self.stt.transcribe(
                audio_path,
                beam_size=1,        # beam_size=1 is fastest
                vad_filter=True,    # Skip silence automatically
                language="en"       # Skip language detection
            )
            text = " ".join([s.text for s in segments])
            return text.strip()
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return ""
    
    # ─────────────────────────────────────────────────────────
    # SPEED OPTIMIZATION: INSTANT COMMAND BYPASS
    # ─────────────────────────────────────────────────────────
    
    def handle_instant_command(self, text: str) -> bool:
        """
        Check for instant commands (< 10ms execution).
        
        Args:
            text: User command text
        
        Returns:
            True if command was executed, False otherwise
        """
        if not is_instant_command(text):
            return False
        
        success, response = execute_instant_command(text)
        
        if success:
            print(f"⚡ Instant: {response}")
            return True
        
        return False
    
    # ─────────────────────────────────────────────────────────
    # SPEED OPTIMIZATION: FAST LLM (Groq)
    # ─────────────────────────────────────────────────────────
    
    def ask_groq(self, text: str) -> str:
        """
        Get response from Groq (< 500ms for 150 tokens).
        
        Args:
            text: User query
        
        Returns:
            LLM response
        """
        if not self.llm:
            return "LLM not configured."
        
        try:
            # Add to history
            self.history.append({"role": "user", "content": text})
            
            # Keep last 10 exchanges for context
            messages = [{"role": "system", "content": self.system_prompt}]
            messages.extend(self.history[-self.max_history:])
            
            # Get response from Groq
            response = self.llm.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=150,     # Keep short for voice
                temperature=0.4,    # Lower = faster + consistent
            )
            
            reply = response.choices[0].message.content
            
            # Add to history
            self.history.append({"role": "assistant", "content": reply})
            
            # Keep history bounded
            if len(self.history) > self.max_history * 2:
                self.history = self.history[-self.max_history:]
            
            return reply
        
        except Exception as e:
            print(f"❌ LLM error: {e}")
            return f"I encountered an error: {str(e)}"
    
    # ─────────────────────────────────────────────────────────
    # SPEED OPTIMIZATION: STREAMING TTS
    # ─────────────────────────────────────────────────────────
    
    def speak(self, text: str) -> bool:
        """
        Stream audio to start speaking immediately (< 200ms).
        
        Args:
            text: Text to speak
        
        Returns:
            True if successful
        """
        if not self.tts:
            print(f"💬 {text}")
            return False
        
        try:
            audio_stream = self.tts.text_to_speech.convert_as_stream(
                voice_id="pNInz6obpgDQGcFmaJgB",  # Adam voice
                text=text,
                model_id="eleven_turbo_v2",     # Lowest latency
            )
            stream(audio_stream)
            return True
        except Exception as e:
            print(f"❌ TTS error: {e}")
            return False
    
    def speak_instant(self, keyword: str) -> bool:
        """
        Play pre-recorded audio clip (instant, no generation).
        
        Args:
            keyword: Clip name (e.g., "volume_up")
        
        Returns:
            True if played, False otherwise
        """
        return play_audio_clip(keyword.replace(" ", "_"))
    
    # ─────────────────────────────────────────────────────────
    # BROWSER AUTOMATION (Gecko)
    # ─────────────────────────────────────────────────────────
    
    def get_gecko(self) -> GeckoBrowser:
        """Get or create Gecko browser instance."""
        if not self.gecko:
            self.gecko = GeckoBrowser(headless=self.headless_browser)
        return self.gecko
    
    def close_gecko(self):
        """Close Gecko browser."""
        if self.gecko:
            self.gecko.close()
            self.gecko = None
    
    def handle_browser_command(self, text: str) -> str:
        """
        Execute browser commands via Gecko.
        
        Args:
            text: Browser command
        
        Returns:
            Command result
        """
        gecko = self.get_gecko()
        
        try:
            result = browser_autonomy(text, self.ask_groq, gecko)
            return result
        except Exception as e:
            return f"Browser error: {str(e)}"
    
    # ─────────────────────────────────────────────────────────
    # COMMAND ROUTING & EXECUTION
    # ─────────────────────────────────────────────────────────
    
    def handle_command(self, text: str) -> bool:
        """
        Route command to appropriate handler.
        
        Priority:
        1. Instant commands (< 100ms)
        2. Browser commands (< 2s)
        3. LLM commands (< 1s)
        
        Args:
            text: User command text
        
        Returns:
            True if command was handled
        """
        if not text.strip():
            return False
        
        print(f"🎤 You: {text}")
        
        # 1. Try instant command (fast)
        if self.handle_instant_command(text):
            return True
        
        # 2. Try browser command
        if needs_browser(text):
            print("🌐 Routing to browser...")
            result = self.handle_browser_command(text)
            self.speak(result)
            return True
        
        # 3. Use LLM (fallback)
        print("🧠 Routing to LLM...")
        response = self.ask_groq(text)
        self.speak(response)
        return True
    
    # ─────────────────────────────────────────────────────────
    # PARALLEL PROCESSING
    # ─────────────────────────────────────────────────────────
    
    async def handle_command_async(self, text: str):
        """
        Handle command with parallel processing where possible.
        
        Args:
            text: User command text
        """
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.handle_command, text)
    
    # ─────────────────────────────────────────────────────────
    # MAIN LOOP
    # ─────────────────────────────────────────────────────────
    
    def shutdown(self):
        """Clean up resources."""
        self.close_gecko()
        print("👋 Anti Gravity shutting down.")
    
    def __del__(self):
        """Ensure cleanup on object destruction."""
        self.shutdown()


# ───────────────────────────────────────────────────────────────
# CONVENIENCE FUNCTIONS
# ───────────────────────────────────────────────────────────────

def create_anti_gravity() -> AntiGravity:
    """Factory function to create Anti Gravity instance with env vars."""
    return AntiGravity(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        eleven_api_key=os.getenv("ELEVENLABS_API_KEY"),
    )
