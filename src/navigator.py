"""
navigator.py
============
Two navigator implementations:

1. BoustrophedonNavigator  – legacy drag/snap approach (kept for reference).
2. CoordNavigator          – uses the in-game coordinate jump dialog
                             (magnifier → enter K, X, Y → Go) to move the map.
                             This is more reliable and preferred.
"""

from __future__ import annotations

import time

import pyautogui

pyautogui.FAILSAFE = True
pyautogui.PAUSE    = 0.0   # timing is controlled explicitly here


# =============================================================================
# CoordNavigator  –  jump-based navigation via the in-game coordinate dialog
# =============================================================================

class CoordNavigator:
    """Navigate the map by entering exact K/X/Y coordinates into the game UI.

    Performs a boustrophedon (serpentine) sweep over the coordinate grid,
    jumping to each position via the magnifier coordinate dialog rather than
    drag-scrolling.
    """

    def __init__(
        self,
        nav_btn:    tuple[int, int],
        k_field:    tuple[int, int],
        x_field:    tuple[int, int],
        y_field:    tuple[int, int],
        go_btn:     tuple[int, int],
        x_min:      int,
        x_max:      int,
        y_min:      int,
        y_max:      int,
        step_x:     int,
        step_y:     int,
        jump_delay: float,
    ):
        self.nav_btn    = nav_btn
        self.k_field    = k_field
        self.x_field    = x_field
        self.y_field    = y_field
        self.go_btn     = go_btn
        self.x_min      = x_min
        self.x_max      = x_max
        self.y_min      = y_min
        self.y_max      = y_max
        self.step_x     = step_x
        self.step_y     = step_y
        self.jump_delay = jump_delay

    def _type_into_field(self, field_pos: tuple[int, int], value: int) -> None:
        """Click a field, clear it, and type the given integer value."""
        pyautogui.click(*field_pos)
        time.sleep(0.1)
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.05)
        pyautogui.typewrite(str(value), interval=0.05)

    def jump_to(self, kingdom_id: int, x: int, y: int) -> None:
        """Open the coordinate dialog and jump to (kingdom_id, x, y)."""
        # 1. Open the dialog
        pyautogui.click(*self.nav_btn)
        time.sleep(0.4)

        # 2. Fill in K, X, Y fields
        self._type_into_field(self.k_field, kingdom_id)
        self._type_into_field(self.x_field, x)
        self._type_into_field(self.y_field, y)

        # 3. Click Go
        pyautogui.click(*self.go_btn)
        time.sleep(self.jump_delay)

    def full_sweep(self, kingdom_id: int):
        """Serpentine sweep over the coordinate grid for the given kingdom.

        Yields
        ------
        (x, y) : (int, int)
            The in-game coordinates the map is now centred on.
        """
        x_positions = list(range(self.x_min, self.x_max + 1, self.step_x))
        y_positions = list(range(self.y_min, self.y_max + 1, self.step_y))

        for col_idx, x in enumerate(x_positions):
            going_down = (col_idx % 2 == 0)
            ys = y_positions if going_down else list(reversed(y_positions))

            for y in ys:
                self.jump_to(kingdom_id, x, y)
                yield x, y





class BoustrophedonNavigator:
    """Executes a serpentine grid sweep using snap-jump mouse drags."""

    def __init__(
        self,
        grid_cols:     int,
        grid_rows:     int,
        snap_step_x:   int,
        snap_step_y:   int,
        settle_delay:  float,
        screen_center: tuple[int, int],
    ):
        self.grid_cols    = grid_cols
        self.grid_rows    = grid_rows
        self.snap_step_x  = snap_step_x
        self.snap_step_y  = snap_step_y
        self.settle_delay = settle_delay
        self.cx, self.cy  = screen_center   # anchor point for all drags

    # ── primitive snap moves ─────────────────────────────────────────────────
    # Each move: reposition cursor to anchor, then drag.
    # Duration 0.04 s = fast enough to feel instant, slow enough not to be
    # misread by the game as a click.

    def _snap(self, dx: int, dy: int) -> None:
        """Generic snap: drag by (dx, dy) relative pixels from anchor."""
        pyautogui.moveTo(self.cx, self.cy, duration=0.0)
        pyautogui.drag(dx, dy, duration=0.04, button="left")
        time.sleep(self.settle_delay)

    def snap_down(self) -> None:
        """Pan the map southward (drag cursor upward)."""
        self._snap(0, -self.snap_step_y)

    def snap_up(self) -> None:
        """Pan the map northward (drag cursor downward)."""
        self._snap(0, self.snap_step_y)

    def snap_right(self) -> None:
        """Pan the map eastward (drag cursor leftward)."""
        self._snap(-self.snap_step_x, 0)

    def snap_left(self) -> None:
        """Pan the map westward (drag cursor rightward)."""
        self._snap(self.snap_step_x, 0)

    # ── full sweep generator ──────────────────────────────────────────────────

    def full_sweep(self):
        """Move the map and yield (col, row) after each position is reached.

        The caller should capture a screen frame immediately after each yield.
        The generator handles all navigation; the caller handles all scanning.

        Yields
        ------
        (col, row) : (int, int)
            Current grid position.  col ∈ [0, grid_cols), row ∈ [0, grid_rows).
        """
        for col in range(self.grid_cols):
            # ── column entry: shift right (except the very first column) ────
            if col > 0:
                self.snap_right()

            going_down = (col % 2 == 0)
            rows = (
                range(self.grid_rows)
                if going_down
                else range(self.grid_rows - 1, -1, -1)
            )

            for i, row in enumerate(rows):
                # ── row entry: vertical snap (except first row of each col) ─
                if i > 0:
                    if going_down:
                        self.snap_down()
                    else:
                        self.snap_up()

                yield col, row

        # Return the map to the sweep origin so the next kingdom starts
        # from a consistent reference point.
        self._return_to_origin()

    # ── origin reset ──────────────────────────────────────────────────────────

    def _return_to_origin(self) -> None:
        """Snap back to the top-left corner of the sweep grid."""
        # Undo horizontal travel
        for _ in range(self.grid_cols - 1):
            self.snap_left()

        # Undo vertical travel: depends on which direction the last column went
        last_col_went_down = (self.grid_cols - 1) % 2 == 0
        if last_col_went_down:
            # Ended at the bottom row → move back to top
            for _ in range(self.grid_rows - 1):
                self.snap_up()
        # If last column went up, we already ended at the top row – nothing to do
