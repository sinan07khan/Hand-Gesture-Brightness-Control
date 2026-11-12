# Hand Gesture Brightness Control

Control your Windows screen brightness hands-free using hand gestures captured by your webcam.

## What You Need

- Windows PC with a working webcam
- Built-in laptop display or an external monitor that supports brightness control
- Python installed on your PC

## How to Run

1. Open a terminal inside the project folder and install the required packages:

   ```bash
   pip install opencv-python numpy mediapipe screen-brightness-control
   ```

2. Start the app:

   ```bash
   python "Hand Gesture Brightness Control.py"
   ```

   *(The included `hand_landmarker.task` model loads from the project folder automatically, or downloads on first run if missing.)*

## How to Use

1. Wait for the **Brightness Control** webcam window to open.
2. Hold **one hand** clearly in front of your webcam—markers and a connecting line will appear on your **thumb tip** and **index fingertip**.
3. Adjust brightness with a pinch gesture:
   - **Bring your thumb and index finger closer together** to **lower** brightness (down to `0%`).
   - **Spread them apart** to **raise** brightness (up to `100%`).
4. Check the live percentage (`Brightness: XX%`) in the top-left corner of the window.
5. Press **`ESC`** or click the window's **`X`** button to exit.

## Tips

- **Lighting**: Use the app in a well-lit space so your hand is easy to detect.
- **Could not access webcam**: Close other apps using your camera (such as Zoom, Teams, or Camera) and allow desktop apps to access the camera in Windows Privacy Settings.
- **External monitor not changing**: Enable **DDC/CI** in your monitor's on-screen settings menu.
