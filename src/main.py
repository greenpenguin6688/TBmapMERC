import cv2
import mss
import numpy as np
import pytesseract
import pydirectinput
import time

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
    template = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)
    if template is None:
        print(f"Template not found: {template_path}")
        return []
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    locations = np.where(result >= threshold)
    matches = list(zip(*locations[::-1]))  # (x, y) positions
    return matches

def main():
    print("Welcome to the Map Scanner!")
    print("Automated map scanning started. Press Ctrl+C in the terminal to stop.")
    template_path = "templates/template1.png"  # Change to your actual template filename
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        while True:
            # Step 1: Click to focus/clear
            pydirectinput.moveTo(960, 540)
            pydirectinput.click()
            time.sleep(0.2)
            # Step 2: Click and drag to scroll the map
            pydirectinput.mouseDown(button='left')
            time.sleep(0.1)
            pydirectinput.moveRel(300, 0)
            time.sleep(0.1)
            pydirectinput.mouseUp(button='left')
            # Step 3: Press ESC to close any popups
            time.sleep(0.2)
            pydirectinput.press('esc')
            # Wait for the map to finish scrolling/rendering
            time.sleep(0.5)
            # Take screenshot and OCR coordinates
            screenshot = np.array(sct.grab(monitor))
            coords_text, _ = extract_coordinates(screenshot)
            if coords_text:
                print(f"Detected Map Coordinates: {coords_text}")
            # --- Template Matching ---
            matches = match_template_on_screen(screenshot, template_path, threshold=0.8)
            if matches:
                print(f"Template found at: {matches}")
            else:
                print("Template not found on this screen.")
            # Wait a bit before next scroll
            time.sleep(1)

if __name__ == "__main__":
    main()