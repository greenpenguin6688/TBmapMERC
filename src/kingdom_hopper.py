"""
kingdom_hopper.py
=================
Switches the in-game map to a different kingdom by automating the game's
"Go to Kingdom" dialog.

Assumed UI flow (adjust config coordinates if your layout differs):
    1. Click KINGDOM_SWITCH_BTN  – opens the search / teleport dialog.
    2. Click KINGDOM_INPUT_FIELD – focus the text entry field.
    3. Select-all + type the kingdom ID as digits.
    4. Click KINGDOM_CONFIRM_BTN – confirms and teleports the map view.
    5. Wait KINGDOM_SWITCH_DELAY seconds for the map to reload.

All (x, y) coordinates are configured in config.py and refer to absolute
screen pixels.
"""

from __future__ import annotations

import time

import pyautogui

pyautogui.FAILSAFE = True
pyautogui.PAUSE    = 0.0   # timing is controlled explicitly here


class KingdomHopper:
    """Automates the in-game UI to teleport the map view to a kingdom."""

    def __init__(
        self,
        switch_btn:   tuple[int, int],
        input_field:  tuple[int, int],
        confirm_btn:  tuple[int, int],
        reload_delay: float,
    ):
        self.switch_btn   = switch_btn
        self.input_field  = input_field
        self.confirm_btn  = confirm_btn
        self.reload_delay = reload_delay

    def jump_to(self, kingdom_id: int) -> None:
        """Interact with the game UI to navigate to *kingdom_id*.

        Parameters
        ----------
        kingdom_id:
            Numeric kingdom ID (e.g. 1024).
        """
        print(f"  [Hopper] Jumping to Kingdom {kingdom_id} …")

        # 1. Open the kingdom navigation dialog
        pyautogui.moveTo(*self.switch_btn)
        time.sleep(0.05)
        pyautogui.click()
        time.sleep(0.5)

        # 2. Focus the input field and clear any previous value
        pyautogui.moveTo(*self.input_field)
        time.sleep(0.05)
        pyautogui.click()
        time.sleep(0.2)
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.05)
        pyautogui.press(["delete", "backspace", "backspace"])
        time.sleep(0.05)

        # 3. Type the kingdom ID one character at a time (typewrite is reliable
        #    for digit strings; interval avoids dropped keystrokes under load)
        pyautogui.typewrite(str(kingdom_id), interval=0.06)
        time.sleep(0.1)

        # 4. Confirm
        pyautogui.moveTo(*self.confirm_btn)
        time.sleep(0.05)
        pyautogui.click()

        # 5. Wait for the map to fully reload before scanning begins
        print(f"  [Hopper] Waiting {self.reload_delay:.1f}s for map reload …")
        time.sleep(self.reload_delay)

        print(f"  [Hopper] Now in Kingdom {kingdom_id}.")
