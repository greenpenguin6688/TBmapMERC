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

# Flask web server setup
app = Flask(__name__)
results = []

@app.route('/')
def index():
    return jsonify(results)

def run_server():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

# --- Utility Functions ---
def extract_coordinates(screenshot):
    height, width, _ = screenshot.shape
    crop_img = screenshot[height-35:height, 0:160]
    gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
    try:
        text = pytesseract.image_to_string(gray, config='--psm 7').strip()
    except pytesseract.pytesseract.TesseractNotFoundError:
        text = "Tesseract Error: Not installed"
    return text, crop_img

def match_template_on_screen(screenshot, template_path, threshold=0.8):
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template is None:
        print(f"Template not found: {template_path}")
        return []
    if screenshot.shape[2] == 4:
        screenshot_bgr = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
    else:
        screenshot_bgr = screenshot
    result = cv2.matchTemplate(screenshot_bgr, template, cv2.TM_CCOEFF_NORMED)
    locations = np.where(result >= threshold)
    matches = list(zip(*locations[::-1]))
    return matches

def extract_k_value(coords_text):
    import re
    match = re.search(r'K[:=\s]*([0-9]+)', coords_text)
    if match:
        return int(match.group(1))
    return None

def screen_spiral_moves(center_x, center_y, screen_width, screen_height, left, right, top, bottom):
    directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]  # right, down, left, up
    x, y = center_x, center_y
    step_w = 600  # Always shift by 100 in x
    step_h = 600  # Always shift by 100 in y
    step = 1
    while True:
        for d in range(4):
            dx, dy = directions[d]
            for _ in range(step):
                x_new = x + dx * step_w
                y_new = y + dy * step_h
                if left < x_new < right and top < y_new < bottom:
                    yield x, y, dx, dy, step_w, step_h
                    x, y = x_new, y_new
            if d % 2 == 1:
                step += 1
        # After each full spiral, increase the step size for a true expanding spiral
        step_w = int(step_w * 1.5)
        step_h = int(step_h * 1.5 )

# --- Main Loop ---
def main():
    print("Welcome to the Map Scanner!")
    print("Automated map scanning started. Press Ctrl+C in the terminal to stop.")
    threading.Thread(target=run_server, daemon=True).start()
    template_path = "../templates/template1.png"
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screen_left, screen_top, screen_width, screen_height = monitor['left'], monitor['top'], monitor['width'], monitor['height']
        margin = 10
        left = screen_left + margin
        right = screen_left + screen_width - margin
        top = screen_top + margin
        bottom = screen_top + screen_height - margin
        center_x = (left + right) // 2
        center_y = (top + bottom) // 2
        spiral = screen_spiral_moves(center_x, center_y, screen_width, screen_height, left, right, top, bottom)
        print("Testing spiral generator...")
        for _ in range(5):
            print(next(spiral))
        print("Starting spiral loop...")
        while True:
            print("In spiral loop...")
            x, y, dx, dy, step_w, step_h = next(spiral)
            print(f"Moving to: ({x}, {y}), dragging by ({dx * step_w}, {dy * step_h})")
            pydirectinput.moveTo(x, y, duration=0.01)
            pydirectinput.mouseDown(button='left')
            time.sleep(0.005)
            pydirectinput.moveRel(dx * step_w, dy * step_h, duration=0.01)
            time.sleep(0.005)
            pydirectinput.mouseUp(button='left')
            time.sleep(0.005)
            pydirectinput.press('esc')
            time.sleep(0.01)
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
            time.sleep(0.01)

if __name__ == "__main__":
    main()