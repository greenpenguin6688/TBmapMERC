import cv2
import mss
import numpy as np
import pytesseract
import pydirectinput
import time
import threading
from flask import Flask, jsonify

# Explicitly set the path to Tesseract (as described in your README)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_coordinates(screenshot):
    """
    Crops out the bottom-left corner of the UI and reads the text.
    You will need to adjust the pixel values (h-100:h, 0:300) to perfectly fit
    the area where the game displays its X, Y coordinates.
    """
    height, width, _ = screenshot.shape
    
    # Crop Region: [Start_Y : End_Y, Start_X : End_X]
    # Based on your Total Battle screenshot, the coordinates "K: 1020 X: 775 Y: 465"
    # are strictly at the very bottom-left corner.
    crop_img = screenshot[height-35:height, 0:160]
    
    # Convert the crop to grayscale for better OCR results
    gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
    
    # Tell Tesseract to look for a single block/line of text (psm 7 is good for small strings)
    try:
        text = pytesseract.image_to_string(gray, config='--psm 7').strip()
    except pytesseract.pytesseract.TesseractNotFoundError:
        text = "Tesseract Error: Not installed"
        
    return text, crop_img

def match_template_on_screen(screenshot, template_path, threshold=0.8):
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)  # Force color
    if template is None:
        print(f"Template not found: {template_path}")
        return []
    # Convert screenshot to BGR if it is BGRA (from mss)
    if screenshot.shape[2] == 4:
        screenshot_bgr = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
    else:
        screenshot_bgr = screenshot
    result = cv2.matchTemplate(screenshot_bgr, template, cv2.TM_CCOEFF_NORMED)
    locations = np.where(result >= threshold)
    matches = list(zip(*locations[::-1]))  # (x, y) positions
    return matches

def extract_k_value(coords_text):
    # Extracts the K value from the OCR string
    import re
    match = re.search(r'K[:=\s]*([0-9]+)', coords_text)
    if match:
        return int(match.group(1))
    return None

# Flask web server setup
app = Flask(__name__)
results = []

@app.route('/')
def index():
    return jsonify(results)

def run_server():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

# Spiral clicker generator
def spiral_moves():
    # Directions: left, up, right, down
    directions = [(-1, 0), (0, -1), (1, 0), (0, 1)]
    x, y = 0, 0
    step = 1
    while True:
        for d in range(4):
            dx, dy = directions[d]
            for _ in range(step):
                x += dx
                y += dy
                yield x, y
            if d % 2 == 1:
                step += 1

def safe_spiral_moves(center_x, center_y, left, right, top, bottom, step_size=80):
    # Spiral: left, up, right, down, expanding
    directions = [(-1, 0), (0, -1), (1, 0), (0, 1)]
    x, y = center_x, center_y
    step = 1
    while True:
        for d in range(4):
            dx, dy = directions[d]
            for _ in range(step):
                x += dx * step_size
                y += dy * step_size
                # Stay within safe zone
                if left < x < right and top < y < bottom:
                    yield x, y, dx, dy
            if d % 2 == 1:
                step += 1

# Flask web server setup
app = Flask(__name__)
results = []

@app.route('/')
def index():
    return jsonify(results)

def run_server():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

# Spiral clicker generator
def spiral_moves():
    # Directions: left, up, right, down
    directions = [(-1, 0), (0, -1), (1, 0), (0, 1)]
    x, y = 0, 0
    step = 1
    while True:
        for d in range(4):
            dx, dy = directions[d]
            for _ in range(step):
                x += dx
                y += dy
                yield x, y
            if d % 2 == 1:
                step += 1

def main():
    print("Welcome to the Map Scanner!")
    print("Automated map scanning started. Press Ctrl+C in the terminal to stop.")
    # Start Flask server in a background thread
    threading.Thread(target=run_server, daemon=True).start()
    template_path = "../templates/template1.png"  # Updated path for running from src directory
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screen_left, screen_top, screen_width, screen_height = monitor['left'], monitor['top'], monitor['width'], monitor['height']
        margin = 100
        left = screen_left + margin
        right = screen_left + screen_width - margin
        top = screen_top + margin
        bottom = screen_top + screen_height - margin
        center_x = (left + right) // 2
        center_y = (top + bottom) // 2
        spiral = safe_spiral_moves(center_x, center_y, left, right, top, bottom, step_size=80)
        while True:
            x, y, dx, dy = next(spiral)
            # Click at (x, y)
            pydirectinput.moveTo(x, y, duration=0.1)
            pydirectinput.click()
            time.sleep(0.05)
            # Drag in the spiral direction (one step)
            pydirectinput.mouseDown(button='left')
            time.sleep(0.05)
            pydirectinput.moveRel(dx * 80, dy * 80, duration=0.1)
            time.sleep(0.05)
            pydirectinput.mouseUp(button='left')
            # Press ESC to close any popups
            time.sleep(0.05)
            pydirectinput.press('esc')
            # Wait for the map to finish scrolling/rendering
            time.sleep(0.2)
            # Take screenshot and OCR coordinates
            screenshot = np.array(sct.grab(monitor))
            coords_text, _ = extract_coordinates(screenshot)
            k_value = extract_k_value(coords_text)
            if k_value is not None and 1010 <= k_value <= 1030:
                matches = match_template_on_screen(screenshot, template_path, threshold=0.8)
                result = {
                    'coords_text': coords_text,
                    'k_value': k_value,
                    'matches': matches
                }
                print(f"[K={k_value}] {coords_text} | Matches: {matches}")
                results.append(result)
            else:
                print(f"[K={k_value}] {coords_text} | Skipped (out of range)")
            time.sleep(0.2)

if __name__ == "__main__":
    main()