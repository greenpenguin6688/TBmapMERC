# =============================================================================
#  TBmapMERC – Configuration
#  Edit ALL user-facing parameters here. No other file needs to be touched
#  for normal operation.
# =============================================================================

from pathlib import Path
import numpy as np

# Absolute project root (one level above src/)
BASE_DIR = Path(__file__).resolve().parent.parent

# =============================================================================
# 1.  KINGDOMS TO SCAN
# =============================================================================
# Add / remove Kingdom IDs as needed. The hopper visits them in order.
KINGDOM_IDS: list[int] = [ 1019 ]                    

# =============================================================================
# 2.  TIER-1  –  HSV Color Thresholding  ("Exchange Purple")
# =============================================================================
# Hue 125-155 captures the purple/violet range used by Mercenary Exchanges.
# Raise PURPLE_PIXEL_THRESHOLD to reduce false positives; lower it to catch
# fainter icons.
HSV_LOWER = np.array([125, 60,  60],  dtype=np.uint8)
HSV_UPPER = np.array([155, 255, 255], dtype=np.uint8)
PURPLE_PIXEL_THRESHOLD: int = 20           # lowered from 150 since the roof is very small at 25% zoom

# =============================================================================
# 3.  TIER-2  –  Template Matching
# =============================================================================
# Place your exchange icon crop in templates/exchange_template.png.
TEMPLATE_PATH: str     = str(BASE_DIR / "templates" / "exchange_template.png")
MATCH_THRESHOLD: float = 0.70              # lowered from 0.82 to be more forgiving

# =============================================================================
# 4.  COORDINATE JUMP NAVIGATION
# =============================================================================
# Instead of drag-scrolling, the scanner uses the in-game coordinate dialog
# (magnifier button → enter K, X, Y → click Go) to jump to each position.
#
# UI positions – set these to where the elements appear on YOUR screen:
COORD_NAV_BTN:  tuple[int, int] = (90, 819)      # magnifier / "Go to coords" button
COORD_K_FIELD:  tuple[int, int] = (864, 488)    # K number input field in the dialog
COORD_X_FIELD:  tuple[int, int] = (960, 488)    # X number input field
COORD_Y_FIELD:  tuple[int, int] = (1071, 488)   # Y number input field
COORD_GO_BTN:   tuple[int, int] = (963, 525)    # "Go" button in the dialog
COORD_NAV_DELAY: float = 0.5                  # seconds to wait after each jump

# In-game coordinate sweep range per kingdom.
# The map origin (0,0) is usually top-left; adjust to your game's layout.
COORD_X_MIN: int  = 0      # leftmost X coordinate to scan
COORD_X_MAX: int  = 1000   # rightmost X coordinate
COORD_Y_MIN: int  = 0      # topmost Y coordinate
COORD_Y_MAX: int  = 1000   # bottommost Y coordinate

# How many in-game units one screen covers at your current zoom level.
# Increase these to skip more tiles per jump (faster but may miss things).
COORD_STEP_X: int = 100    # in-game X units per horizontal step
COORD_STEP_Y: int = 100    # in-game Y units per vertical step

# =============================================================================
# 5.  STATE MANAGEMENT & COOLDOWN
# =============================================================================
SCAN_LOG_PATH: str  = str(BASE_DIR / "scan_state.json")
FIND_LOG_PATH: str  = str(BASE_DIR / "finds_log.json")
COOLDOWN_SECONDS: int = 300          # skip a position if scanned < 5 min ago

# =============================================================================
# 6.  OCR COORDINATE REGION
# =============================================================================
# Screen rectangle (screen-px) where the game renders "K:XXXX  X:YYY  Y:ZZZ".
# Adjust left/top/width/height to match your resolution and HUD layout.
COORDS_REGION: dict = {"left": 0, "top": 0, "width": 220, "height": 36}

# =============================================================================
# 7.  KINGDOM-HOPPER  –  UI Interaction Coordinates  (screen-px)
# =============================================================================
# Tune each (x, y) pair to match your screen resolution / game window layout.
KINGDOM_SWITCH_BTN:  tuple[int, int] = (960, 1050)   # opens the "Go to Kingdom" dialog
KINGDOM_INPUT_FIELD: tuple[int, int] = (960,  540)   # text field inside the dialog
KINGDOM_CONFIRM_BTN: tuple[int, int] = (1060, 580)   # "Go" / confirm button

# =============================================================================
# 8.  NOTIFICATIONS
# =============================================================================
# Set to an absolute path of a .wav file for a custom sound, or None for the
# default OS beep.
ALERT_SOUND_PATH: str | None = None      # e.g. str(BASE_DIR / "assets" / "alert.wav")

# =============================================================================
# 9.  TIMING
# =============================================================================
SNAP_SETTLE_DELAY:    float = 0.06    # seconds to wait after each snap move (legacy)
KINGDOM_SWITCH_DELAY: float = 3.0    # seconds to wait for the map to reload
FRAME_COOLDOWN:       float = 0.0    # extra sleep between frames (0 = max speed)

# OCR is called every N rows to keep calibration fresh without hammering CPU.
OCR_CALIBRATION_INTERVAL: int = 10

# =============================================================================
# 10.  DISPLAY / INPUT
# =============================================================================
MONITOR_INDEX: int = 1    # 0 = all monitors combined, 1 = primary monitor

# =============================================================================
# 11.  TESSERACT
# =============================================================================
TESSERACT_PATH: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
