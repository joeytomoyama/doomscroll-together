# import pyautogui
import time
import random
import subprocess

BROWSER_CMD = ["firefox", "--new-tab"]

# Enable pyautogui failsafe
# pyautogui.FAILSAFE = True

SAFETY_PAUSE = 0.1


# def openURLLikeHuman(url: str, time_seconds: float):
#     """
#     Type out a URL with human-like inconsistency.
    
#     The typing speed varies throughout, with pauses between characters
#     spread across the total time specified.
    
#     Args:
#         url: The URL string to type
#         time_seconds: Total time in seconds to spend typing the URL
#     """
#     time.sleep(SAFETY_PAUSE)
    
#     char_count = len(url)
#     if char_count == 0:
#         return
    
#     # Calculate base interval between characters
#     base_interval = time_seconds / char_count

#     # hot key control L
#     pyautogui.hotkey('ctrl', 'l')
#     time.sleep(0.2)  # brief pause after focusing address bar
    
#     for char in url:
#         # Add random variation to typing speed (±50% of base interval)
#         variation = random.uniform(0.5, 1.5)
#         interval = base_interval * variation
        
#         # Occasionally add longer pauses (like thinking)
#         if random.random() < 0.1:  # 10% chance of longer pause
#             interval *= random.uniform(1.5, 3.0)
        
#         # Type the character
#         pyautogui.typewrite(char, interval=0.05)
        
#         # Sleep for the calculated interval
#         time.sleep(interval)


# def click(x: int, y: int, delay: float = 0.1):
#     """
#     Click at coordinates with a delay.
    
#     Args:
#         x: X coordinate
#         y: Y coordinate
#         delay: Delay before clicking (for human-like behavior)
#     """
#     time.sleep(delay)
#     pyautogui.click(x, y)


# def moveMouse(x: int, y: int, duration: float = 0.5):
#     """
#     Move mouse to coordinates over a duration.
    
#     Args:
#         x: Target X coordinate
#         y: Target Y coordinate
#         duration: Time to take moving the mouse
#     """
#     pyautogui.moveTo(x, y, duration=duration)


# def typeText(text: str, interval: float = 0.05):
#     """
#     Type text at a consistent speed.
    
#     Args:
#         text: Text to type
#         interval: Delay between characters
#     """
#     time.sleep(SAFETY_PAUSE)
#     pyautogui.typewrite(text, interval=interval)


# def press(key: str):
#     """
#     Press a keyboard key.
    
#     Args:
#         key: Key name (e.g., 'enter', 'tab', 'escape')
#     """
#     time.sleep(SAFETY_PAUSE)
#     pyautogui.press(key)


# def hotkey(*keys):
#     """
#     Press multiple keys simultaneously (e.g., Ctrl+C).
    
#     Args:
#         *keys: Key names (e.g., 'ctrl', 'c')
#     """
#     time.sleep(SAFETY_PAUSE)
#     pyautogui.hotkey(*keys)


def open_in_firefox(url: str):
    try:
        subprocess.Popen(BROWSER_CMD + [url])
        print(f"[OPEN] {url}")
    except FileNotFoundError:
        print("[ERROR] Firefox command not found. Adjust BROWSER_CMD.")
    except Exception as e:
        print(f"[ERROR] Failed to open URL: {e}")
