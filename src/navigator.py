"""
navigator.py
============
Boustrophedon (serpentine) map navigator using discrete "snap" moves.

Pattern per kingdom sweep
--------------------------
    Col 0 : top → bottom   (snap DOWN each row)
    shift right one column
    Col 1 : bottom → top   (snap UP each row)
    shift right one column
    Col 2 : top → bottom
    …

"Snap Navigation"
-----------------
Rather than smooth pyautogui drags (which produce many intermediate frames
and misalign the grid), each move is a single fast drag over a fixed
screen-pixel distance.  The map moves by exactly one grid step per call,
keeping frames edge-aligned for reliable template comparison.

    pyautogui drag direction  →  map pan direction
    drag UP   (dy < 0)        →  map scrolls DOWN  (reveals southern tiles)
    drag DOWN (dy > 0)        →  map scrolls UP    (reveals northern tiles)
    drag LEFT (dx < 0)        →  map scrolls RIGHT
    drag RIGHT(dx > 0)        →  map scrolls LEFT
"""

from __future__ import annotations

import time

import pyautogui

# Safety: moving mouse to top-left corner raises FailSafeException and
# terminates the script – useful emergency stop.
pyautogui.FAILSAFE = True
pyautogui.PAUSE    = 0.0   # disable implicit pauses; we control timing ourselves


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
