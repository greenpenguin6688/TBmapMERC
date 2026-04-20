"""
main.py
=======
TBmapMERC – Total Battle Mercenary Exchange Scanner
====================================================

Entry point and main orchestration loop.

Usage
-----
    cd d:\\projects\\TBmapMERC
    python src/main.py

The script gives you a 3-second countdown so you can switch focus to the
game window before automation begins.  Press Ctrl+C at any time to stop
cleanly.

Module overview
---------------
    config.py          – All user-facing parameters (edit this first)
    scanner.py         – Two-tier colour + template scanner
    navigator.py       – Boustrophedon (serpentine) snap-jump navigator
    kingdom_hopper.py  – Automates the in-game "Go to Kingdom" dialog
    state_manager.py   – JSON-backed cooldown / find log
    ocr_calibrator.py  – OCR sub-routine for coordinate auto-calibration
    notifier.py        – Audible alert on confirmed finds
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import mss
import numpy as np

# ── ensure src/ is on the path when running from the project root ─────────────
_SRC = Path(__file__).resolve().parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import config
from kingdom_hopper  import KingdomHopper
from navigator       import CoordNavigator
from notifier        import play_alert
from ocr_calibrator  import format_coords, read_map_coords
from scanner         import TwoTierScanner
from state_manager   import StateManager


# ── helpers ───────────────────────────────────────────────────────────────────

def _position_key(kingdom_id: int, col: int, row: int) -> str:
    return f"K{kingdom_id}_{col}_{row}"


def _countdown(seconds: int) -> None:
    """Give the user time to switch to the game window."""
    for i in range(seconds, 0, -1):
        print(f"  Starting in {i}…", end="\r", flush=True)
        time.sleep(1)
    print(" " * 30, end="\r")   # clear the countdown line


def _print_header() -> None:
    line = "=" * 60
    print(line)
    print("  TBmapMERC  –  Mercenary Exchange Scanner")
    print(line)
    kingdoms = ", ".join(str(k) for k in config.KINGDOM_IDS)
    print(f"  Kingdoms : {kingdoms}")
    print(f"  Grid     : {config.GRID_COLS} cols × {config.GRID_ROWS} rows")
    print(f"  Cooldown : {config.COOLDOWN_SECONDS}s")
    print(f"  Template : {config.TEMPLATE_PATH}")
    print(line)


# ── main orchestration ────────────────────────────────────────────────────────

def main() -> None:
    _print_header()

    # ── instantiate all modules ───────────────────────────────────────────────
    state = StateManager(
        scan_log_path = config.SCAN_LOG_PATH,
        find_log_path = config.FIND_LOG_PATH,
        cooldown      = config.COOLDOWN_SECONDS,
    )

    scanner = TwoTierScanner(
        hsv_lower       = config.HSV_LOWER,
        hsv_upper       = config.HSV_UPPER,
        pixel_threshold = config.PURPLE_PIXEL_THRESHOLD,
        template_path   = config.TEMPLATE_PATH,
        match_threshold = config.MATCH_THRESHOLD,
    )

    hopper = KingdomHopper(
        switch_btn   = config.KINGDOM_SWITCH_BTN,
        input_field  = config.KINGDOM_INPUT_FIELD,
        confirm_btn  = config.KINGDOM_CONFIRM_BTN,
        reload_delay = config.KINGDOM_SWITCH_DELAY,
    )

    print("\nPress Ctrl+C at any time to stop.")
    _countdown(3)

    total_finds  = 0
    total_scanned = 0

    with mss.mss() as sct:
        monitor  = sct.monitors[config.MONITOR_INDEX]

        nav = CoordNavigator(
            nav_btn    = config.COORD_NAV_BTN,
            k_field    = config.COORD_K_FIELD,
            x_field    = config.COORD_X_FIELD,
            y_field    = config.COORD_Y_FIELD,
            go_btn     = config.COORD_GO_BTN,
            x_min      = config.COORD_X_MIN,
            x_max      = config.COORD_X_MAX,
            y_min      = config.COORD_Y_MIN,
            y_max      = config.COORD_Y_MAX,
            step_x     = config.COORD_STEP_X,
            step_y     = config.COORD_STEP_Y,
            jump_delay = config.COORD_NAV_DELAY,
        )

        # ── kingdom loop ──────────────────────────────────────────────────────
        for kingdom_id in config.KINGDOM_IDS:
            sep = "─" * 60
            x_steps = len(range(config.COORD_X_MIN, config.COORD_X_MAX + 1, config.COORD_STEP_X))
            y_steps = len(range(config.COORD_Y_MIN, config.COORD_Y_MAX + 1, config.COORD_STEP_Y))
            print(f"\n{sep}")
            print(f"  KINGDOM {kingdom_id}  "
                  f"({x_steps} x-steps × {y_steps} y-steps, "
                  f"{x_steps * y_steps} positions)")
            print(sep)

            hopper.jump_to(kingdom_id)

            kingdom_finds = 0

            # ── coordinate sweep ──────────────────────────────────────────────
            for x, y in nav.full_sweep(kingdom_id):
                # ── cooldown gate ─────────────────────────────────────────────
                if state.is_on_cooldown(kingdom_id, x, y):
                    continue

                # ── capture frame ─────────────────────────────────────────────
                frame = np.array(sct.grab(monitor))

                # ── OCR calibration (every N y-steps at x_min) ────────────────
                if x == config.COORD_X_MIN and y % (config.OCR_CALIBRATION_INTERVAL * config.COORD_STEP_Y) == 0:
                    kid, mx, my = read_map_coords(
                        sct, config.COORDS_REGION, config.TESSERACT_PATH
                    )
                    print(f"    [OCR] {format_coords(kid, mx, my)}")

                # ── two-tier scan ─────────────────────────────────────────────
                pos_key = _position_key(kingdom_id, x, y)
                triggered, matches = scanner.scan(frame, pos_key)

                state.mark_scanned(kingdom_id, x, y)
                total_scanned += 1

                if not triggered or not matches:
                    if config.FRAME_COOLDOWN:
                        time.sleep(config.FRAME_COOLDOWN)
                    continue

                # ── CONFIRMED FIND ────────────────────────────────────────────
                kid_ocr, mx_ocr, my_ocr = read_map_coords(
                    sct, config.COORDS_REGION, config.TESSERACT_PATH
                )
                map_str = format_coords(kid_ocr, mx_ocr, my_ocr)

                for match_xy in matches:
                    state.log_find(kingdom_id, map_str, match_xy)
                    total_finds  += 1
                    kingdom_finds += 1

                    print(
                        f"\n  *** EXCHANGE FOUND ***"
                        f"  {map_str}"
                        f"  coord=({x},{y})"
                        f"  screen={match_xy}"
                    )
                    play_alert(config.ALERT_SOUND_PATH)

            print(
                f"\n  Kingdom {kingdom_id} complete.  "
                f"Finds this kingdom: {kingdom_finds}"
            )

    # ── summary ───────────────────────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print(f"  Scan complete.")
    print(f"  Positions scanned : {total_scanned}")
    print(f"  Exchanges found   : {total_finds}")
    print(f"  Find log          : {config.FIND_LOG_PATH}")
    print(f"  Scan state        : {config.SCAN_LOG_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Stopped by user.")
    except Exception as exc:
        print(f"\n  [Fatal] {exc}")
        raise


