"""
Example: Integration with Jarvis Assistant
Shows how to use the listening UI in your main assistant loop
"""

from ui.listening_ui import show_listening, show_responding, hide
import time


def example_with_listening_ui():
    """Example showing how to integrate the UI with Jarvis"""
    
    print("Starting assistant with UI...")
    
    # When user wakes Jarvis/starts listening
    show_listening()
    print("[UI] Showing listening state...")
    time.sleep(3)
    
    # When Jarvis starts processing/speaking
    show_responding()
    print("[UI] Switched to responding state...")
    time.sleep(2)
    
    # Hide when done
    hide()
    print("[UI] Hidden")


if __name__ == "__main__":
    example_with_listening_ui()
