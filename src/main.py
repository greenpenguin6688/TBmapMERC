import cv2
import mss
import numpy as np
import pytesseract

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
    # Example: Bottom 100 pixels, left-most 300 pixels
    crop_img = screenshot[height-100:height, 0:300]
    
    # Convert the crop to grayscale for better OCR results
    gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
    
    # Tell Tesseract to look for a single block/line of text (psm 7 is good for small strings)
    try:
        text = pytesseract.image_to_string(gray, config='--psm 7').strip()
    except pytesseract.pytesseract.TesseractNotFoundError:
        text = "Tesseract Error: Not installed"
        
    return text, crop_img

def main():
    print("Welcome to the Map Scanner!")
    print("Starting screen capture... Press 'q' in the OpenCV window to exit.")
    
    with mss.mss() as sct:
        # Get information of monitor 1
        monitor = sct.monitors[1]
        
        while True:
            # Grab the screen data
            screenshot = np.array(sct.grab(monitor))
            
            # --- 1. Coordinate Tracking (OCR) ---
            coords_text, coords_crop = extract_coordinates(screenshot)
            if coords_text:
                print(f"Detected Map Coordinates: {coords_text}")
            
            # Show the cropped area in a separate tiny window so you can calibrate its size
            cv2.imshow('UI Crop (Adjust me!)', coords_crop)
            
            # Display the main screen
            cv2.imshow('Map Scanner Preview (Press q to quit)', screenshot)
            
            # Press 'q' to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()