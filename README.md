# Map Scanner (TBmapMERC)

A real-time game map scanning tool built with Python. This project uses OpenCV for template matching (finding specific buildings or objects on the map) and Tesseract OCR to read live coordinate data directly from the game screen.

## Features
- **High-Speed Screen Capture:** Uses `mss` to continuously capture the game screen with minimal lag.
- **Coordinate Tracking:** Uses Optical Character Recognition (OCR) to read the user's current `X, Y` map coordinates from the game's UI.
- **Building Detection (WIP):** Uses OpenCV Template Matching to scan the map for specific structures at a fixed zoom level (e.g., 25%).

## Prerequisites

1. **Python 3.x**
2. **Tesseract OCR (Required for Windows)**
   - Download the Windows installer here: [Tesseract OCR for Windows](https://github.com/UB-Mannheim/tesseract/wiki)
   - Install it using the default path (`C:\Program Files\Tesseract-OCR\tesseract.exe`).

## Setup

1. Clone this repository.
2. Create a Python virtual environment:
   ```bash
   python -m venv venv
   ```
3. Activate your Python virtual environment (Windows PowerShell):
   ```bash
   .\venv\Scripts\Activate.ps1
   ```
   *(Note: If you get a script execution policy error, you may need to run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` first).*
4. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Place small, cropped images of the buildings you want to detect into the `templates/` folder.
2. Run the main script:
   ```bash
   python src/main.py
   ```
3. The tool will begin scanning your primary monitor.

## How it works
1. The script takes continuous screenshots.
2. It crops out the bottom-left corner of the UI and reads the text (using Tesseract) to determine the camera's current central coordinate.
3. It scans the rest of the screen using OpenCV to look for pixel patterns that match your saved `templates/`.
4. It calculates the offset and translates the pixel matches into in-game coordinate locations.
