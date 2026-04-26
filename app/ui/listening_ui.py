"""
Siri-like Listening UI for Jarvis Voice Assistant
Floating popup with animated orb, rings, waveform, and status indicator
"""

import tkinter as tk
from tkinter import Canvas
import threading
import time
import math
from typing import Optional


class ListeningUI:
    """Siri-style listening UI with animated orb and waveform visualization"""
    
    def __init__(self, width: int = 300, height: int = 380):
        """Initialize the listening UI window
        
        Args:
            width: Window width in pixels
            height: Window height in pixels
        """
        self.width = width
        self.height = height
        self.root: Optional[tk.Tk] = None
        self.canvas: Optional[Canvas] = None
        self.thread: Optional[threading.Thread] = None
        self.running = False
        self.state = "listening"  # "listening" or "responding"
        
        # Animation state
        self.pulse_value = 0
        self.pulse_direction = 1
        self.ring_angle = 0
        self.waveform_values = [30, 40, 50, 60, 50, 40, 30, 35] + [25] * 8
        self.blink_state = False
        self.blink_timer = 0
        
        # Dragging state
        self.drag_data = {"x": 0, "y": 0}
        
    def _create_window(self):
        """Create the main tkinter window"""
        self.root = tk.Tk()
        self.root.geometry(f"{self.width}x{self.height}+{self._get_bottom_right_position()[0]}+{self._get_bottom_right_position()[1]}")
        
        # Remove title bar and set properties
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-transparentcolor', '#111214')
        
        # Create canvas with semi-transparent background
        self.canvas = Canvas(
            self.root,
            width=self.width,
            height=self.height,
            bg='#111214',
            highlightthickness=0,
            cursor="hand2"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind mouse events for dragging
        self.canvas.bind("<Button-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        
    def _get_bottom_right_position(self) -> tuple:
        """Get bottom-right corner position (with padding)"""
        if not self.root:
            return (1400, 700)  # Fallback position
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        padding = 30
        x = screen_width - self.width - padding
        y = screen_height - self.height - padding
        return (x, y)
    
    def _on_press(self, event):
        """Start dragging"""
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
    
    def _on_drag(self, event):
        """Handle window dragging"""
        if not self.root:
            return
        
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]
        
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        
        self.root.geometry(f"+{x}+{y}")
    
    def _draw_frame(self):
        """Draw a single animation frame"""
        if not self.canvas or not self.root:
            return
        
        self.canvas.delete("all")
        
        center_x = self.width / 2
        center_y = 100
        
        # Draw expanding rings
        self._draw_rings(center_x, center_y)
        
        # Draw glowing orb
        self._draw_orb(center_x, center_y)
        
        # Draw waveform
        self._draw_waveform(center_x, 230)
        
        # Draw status text
        self._draw_status(center_x)
        
        # Update animation state
        self._update_animation_state()
    
    def _draw_rings(self, center_x: float, center_y: float):
        """Draw expanding ring animations"""
        for i in range(3):
            ring_radius = 40 + (i * 20) + (self.pulse_value * 15)
            
            # Calculate alpha based on ring expansion
            max_radius = 120
            alpha = int(255 * (1 - (ring_radius / max_radius)))
            alpha = max(20, min(alpha, 100))
            
            # Draw ring (approximated with oval)
            color = self._hex_to_rgb("#7C3AED")
            color_str = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
            
            x0 = center_x - ring_radius
            y0 = center_y - ring_radius
            x1 = center_x + ring_radius
            y1 = center_y + ring_radius
            
            self.canvas.create_oval(
                x0, y0, x1, y1,
                outline=color_str,
                width=2
            )
    
    def _draw_orb(self, center_x: float, center_y: float):
        """Draw the central glowing orb"""
        orb_radius = 30 + (self.pulse_value * 5)
        
        # Outer glow
        glow_radius = orb_radius + 15
        self.canvas.create_oval(
            center_x - glow_radius,
            center_y - glow_radius,
            center_x + glow_radius,
            center_y + glow_radius,
            fill="#7C3AED",
            outline="",
            stipple="gray50"
        )
        
        # Main orb
        self.canvas.create_oval(
            center_x - orb_radius,
            center_y - orb_radius,
            center_x + orb_radius,
            center_y + orb_radius,
            fill="#9F7AEA",
            outline="#E9D5FF",
            width=2
        )
        
        # Inner highlight
        highlight_radius = orb_radius * 0.4
        self.canvas.create_oval(
            center_x - highlight_radius,
            center_y - highlight_radius - (orb_radius * 0.3),
            center_x + highlight_radius,
            center_y - highlight_radius + (orb_radius * 0.3),
            fill="#E9D5FF",
            outline=""
        )
    
    def _draw_waveform(self, center_x: float, top_y: float):
        """Draw audio waveform bars"""
        bar_width = 6
        bar_spacing = 11
        num_bars = 16
        
        # Animate waveform by shifting and cycling values
        for i in range(num_bars):
            # Get bar height from waveform_values (with oscillation)
            idx = (i + int(time.time() * 10)) % len(self.waveform_values)
            base_height = self.waveform_values[idx]
            
            # Add sine wave oscillation for bouncing effect
            oscillation = 15 * math.sin(time.time() * 3 + i * 0.3)
            height = base_height + oscillation
            height = max(15, min(height, 60))
            
            x = center_x - (num_bars * bar_spacing / 2) + (i * bar_spacing)
            
            # Draw bar with gradient effect
            bar_color = "#A78BFA" if i % 2 == 0 else "#9F7AEA"
            self.canvas.create_rectangle(
                x - bar_width / 2,
                top_y - height,
                x + bar_width / 2,
                top_y,
                fill=bar_color,
                outline=""
            )
    
    def _draw_status(self, center_x: float):
        """Draw status text with blinking indicator"""
        y_pos = 320
        
        # Blinking dot
        if self.blink_state:
            dot_color = "#EC4899"
        else:
            dot_color = "#EC4899"
        
        self.canvas.create_oval(
            center_x - 95,
            y_pos - 8,
            center_x - 85,
            y_pos + 2,
            fill=dot_color,
            outline=""
        )
        
        # Main text
        if self.state == "listening":
            text = "Listening..."
            subtitle = "Speak your command"
        else:
            text = "Responding..."
            subtitle = "Processing your request"
        
        self.canvas.create_text(
            center_x - 70,
            y_pos,
            text=text,
            font=("Segoe UI", 11, "bold"),
            fill="#FFFFFF",
            anchor="w"
        )
        
        # Subtitle
        self.canvas.create_text(
            center_x,
            y_pos + 28,
            text=subtitle,
            font=("Segoe UI", 9),
            fill="#A0AEC0",
            anchor="center"
        )
    
    def _update_animation_state(self):
        """Update animation values for next frame"""
        # Pulse the orb
        self.pulse_value += 0.05 * self.pulse_direction
        if self.pulse_value >= 1:
            self.pulse_direction = -1
        elif self.pulse_value <= 0:
            self.pulse_direction = 1
        
        # Blink indicator
        self.blink_timer += 1
        if self.blink_timer % 30 == 0:
            self.blink_state = not self.blink_state
        
        # Update ring animation
        self.ring_angle = (self.ring_angle + 5) % 360
        
        # Cycle waveform values
        self.waveform_values = self.waveform_values[1:] + [self.waveform_values[0]]
    
    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _animation_loop(self):
        """Main animation loop running in background thread"""
        target_fps = 60
        frame_time = 1.0 / target_fps
        
        while self.running and self.root:
            try:
                self._draw_frame()
                self.root.update()
                time.sleep(frame_time)
            except Exception as e:
                print(f"Animation error: {e}")
                break
    
    def _run_window(self):
        """Run the main window loop"""
        try:
            self._create_window()
            self._animation_loop()
        except Exception as e:
            print(f"UI Error: {e}")
    
    def show_listening(self):
        """Show the listening UI and start animation"""
        if self.running:
            self.state = "listening"
            return
        
        self.running = True
        self.state = "listening"
        
        self.thread = threading.Thread(target=self._run_window, daemon=True)
        self.thread.start()
        
        # Give window time to initialize
        time.sleep(0.5)
    
    def show_responding(self):
        """Switch to responding state"""
        self.state = "responding"
    
    def hide(self):
        """Hide the UI and stop animation"""
        self.running = False
        
        if self.root:
            try:
                self.root.destroy()
            except:
                pass
        self.root = None
        self.canvas = None
        
        # Wait for thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)


# Global instance for easy access
_listening_ui: Optional[ListeningUI] = None


def initialize_ui():
    """Initialize the global UI instance"""
    global _listening_ui
    _listening_ui = ListeningUI()
    return _listening_ui


def show_listening():
    """Show listening state"""
    global _listening_ui
    if _listening_ui is None:
        _listening_ui = ListeningUI()
    _listening_ui.show_listening()


def show_responding():
    """Show responding state"""
    global _listening_ui
    if _listening_ui is None:
        return
    _listening_ui.show_responding()


def hide():
    """Hide the UI"""
    global _listening_ui
    if _listening_ui is None:
        return
    _listening_ui.hide()


if __name__ == "__main__":
    # Demo mode
    ui = ListeningUI()
    ui.show_listening()
    
    time.sleep(3)
    ui.show_responding()
    
    time.sleep(3)
    ui.hide()
