"""
notifier.py
===========
Sound alert for confirmed Exchange finds.

Priority:
  1. Custom .wav file via winsound.PlaySound  (Windows, non-blocking)
  2. OS beep via winsound.Beep               (Windows, built-in)
  3. Terminal bell character                  (cross-platform fallback)
"""

from __future__ import annotations

import sys


def play_alert(sound_path: str | None = None) -> None:
    """Play an audible notification.

    Parameters
    ----------
    sound_path:
        Absolute path to a .wav file, or None to use the default OS beep.
    """
    try:
        if sys.platform == "win32":
            import winsound  # stdlib on Windows – no installation required

            if sound_path:
                winsound.PlaySound(
                    sound_path,
                    winsound.SND_FILENAME | winsound.SND_ASYNC,
                )
            else:
                # Three short beeps to cut through background noise
                for freq, dur in [(800, 150), (1000, 150), (1200, 250)]:
                    winsound.Beep(freq, dur)
        else:
            # POSIX fallback: terminal bell
            print("\a\a\a", end="", flush=True)

    except Exception as exc:
        # Never let a sound failure crash the scanner
        print(f"  [Notifier] Could not play alert: {exc}")
