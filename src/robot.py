import pyautogui
import time
import random
import subprocess
# import sleep
from time import sleep
import math

BROWSER_CMD = ["firefox", "--new-tab"]
# TODO: programmatically focus firefox with xdotool if needed

# Enable pyautogui failsafe
# pyautogui.FAILSAFE = True

SAFETY_PAUSE = 0.1


# def openURLLikeHuman(url: str, time_seconds: float):
#     """
#     Type out a URL with human-like inconsistency.

#     The typing speed varies throughout, with pauses between characters,
#     but the total typing time equals time_seconds.
#     """
#     time.sleep(SAFETY_PAUSE)

#     char_count = len(url)
#     if char_count == 0 or time_seconds <= 0:
#         return

#     # Focus address bar
#     pyautogui.hotkey('ctrl', 'l')
#     time.sleep(0.2)

#     # --- Generate human-like random delays ---
#     # Base random weights (not yet time-based)
#     delays = []
#     for _ in range(char_count):
#         weight = random.uniform(0.1, 3.0)

#         # Occasional thinking pause
#         if random.random() < 0.1:
#             weight *= random.uniform(5.0, 8.0)

#         delays.append(weight)

#     # Normalize delays so total equals time_seconds
#     total_weight = sum(delays)
#     delays = [(d / total_weight) * time_seconds for d in delays]

#     # --- Type characters with computed delays ---
#     for char, delay in zip(url, delays):
#         pyautogui.typewrite(char)   # no internal interval
#         time.sleep(delay)
#         print(delay)

#     pyautogui.press('enter')

def openURLLikeHuman(url: str):#, time_seconds: float):
    time_seconds = 1.0
    time.sleep(SAFETY_PAUSE)

    char_count = len(url)
    if char_count == 0 or time_seconds <= 0:
        return

    pyautogui.hotkey('ctrl', 'l')
    time.sleep(SAFETY_PAUSE)

    # # Generate human-like delay weights (log-normal)
    # delays = [
    #     random.lognormvariate(mu=-1.4, sigma=2.4)
    #     for _ in range(char_count)
    # ]

    # # Occasional extreme pauses
    # for i in range(char_count):
    #     if random.random() < 0.05:
    #         delays[i] *= random.uniform(4.0, 6.0)

    # # Normalize
    # print("[DEBUG] Raw delays:", sum(delays))
    # total = sum(delays)
    # delays = [(d / total) * (time_seconds - SAFETY_PAUSE * 2) for d in delays]
    # print("[DEBUG] Normalized delays:", sum(delays))

    # if (len(url) >= 36):
    #     delays = [d * 0 for d in delays]  # speed up for long URLs

    # for char, delay in zip(url, delays):
    pyautogui.typewrite(url, interval=0.05)
        # time.sleep(delay)

    pyautogui.press('enter')

def click(x: int, y: int, delay: float = 0.1):
    """
    Click at coordinates with a delay.
    
    Args:
        x: X coordinate
        y: Y coordinate
        delay: Delay before clicking (for human-like behavior)
    """
    time.sleep(delay)
    pyautogui.click(x, y)


def moveMouse(x: int, y: int, duration: float = 0.5):
    """
    Move mouse to coordinates over a duration.
    
    Args:
        x: Target X coordinate
        y: Target Y coordinate
        duration: Time to take moving the mouse
    """
    pyautogui.moveTo(x, y, duration=duration)


def typeText(text: str, interval: float = 0.05):
    """
    Type text at a consistent speed.
    
    Args:
        text: Text to type
        interval: Delay between characters
    """
    time.sleep(SAFETY_PAUSE)
    pyautogui.typewrite(text, interval=interval)


def press(key: str):
    """
    Press a keyboard key.
    
    Args:
        key: Key name (e.g., 'enter', 'tab', 'escape')
    """
    time.sleep(SAFETY_PAUSE)
    pyautogui.press(key)


def hotkey(*keys):
    """
    Press multiple keys simultaneously (e.g., Ctrl+C).
    
    Args:
        *keys: Key names (e.g., 'ctrl', 'c')
    """
    time.sleep(SAFETY_PAUSE)
    pyautogui.hotkey(*keys)


def open_in_firefox(url: str):
    try:
        subprocess.Popen(BROWSER_CMD + [url])
        print(f"[OPEN] {url}")
    except FileNotFoundError:
        print("[ERROR] Firefox command not found. Adjust BROWSER_CMD.")
    except Exception as e:
        print(f"[ERROR] Failed to open URL: {e}")


# sleep(2)
# openURLLikeHuman("https://tiktok.com/@user/video/12345")