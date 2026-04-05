import pyautogui
import time
import random
import subprocess
# import sleep
from time import sleep
import math
from src import store

BROWSER_CMD = ["firefox", "--new-tab"]
# TODO: programmatically focus firefox with xdotool if needed

# Enable pyautogui failsafe
# pyautogui.FAILSAFE = True

SAFETY_PAUSE = 0.1


def is_dev_mode() -> bool:
    return bool(getattr(store, "DEV", False))


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
#     hotkey('ctrl', 'l')
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

#     press('enter')

def openURLLikeHuman(url: str):#, time_seconds: float):
    time_seconds = 1.0
    time.sleep(SAFETY_PAUSE)

    char_count = len(url)
    if char_count == 0 or time_seconds <= 0:
        return

    # focus address bar and clear it
    hotkey('ctrl', 'l')
    hotkey('ctrl', 'a')
    press('backspace')
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
    typewrite(url, interval=0.05)
        # time.sleep(delay)

    press('enter')


def press(key: str):
    """
    Press a keyboard key.
    
    Args:
        key: Key name (e.g., 'enter', 'tab', 'escape')
    """
    time.sleep(SAFETY_PAUSE)
    if is_dev_mode():
        print(f"[DEV][press] {key}")
        return
    pyautogui.press(key)


def hotkey(*keys):
    """
    Press multiple keys simultaneously (e.g., Ctrl+C).
    
    Args:
        *keys: Key names (e.g., 'ctrl', 'c')
    """
    time.sleep(SAFETY_PAUSE)
    if is_dev_mode():
        print(f"[DEV][hotkey] {' + '.join(keys)}")
        return
    pyautogui.hotkey(*keys)


def typewrite(text: str, interval: float = 0.1):
    """
    Type out text with a delay between characters.
    
    Args:
        text: The string to type.
        interval: Delay in seconds between each character.
    """
    time.sleep(SAFETY_PAUSE)
    if is_dev_mode():
        print(f"[DEV][typewrite] {text}")
        return
    pyautogui.typewrite(text, interval=interval)


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