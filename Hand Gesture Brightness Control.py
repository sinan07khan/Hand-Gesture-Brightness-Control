import ctypes
import os
import sys
import urllib.request
import cv2
import numpy as np
import mediapipe as mp
import screen_brightness_control as sbc


def _get_app_dir() -> str:
    """Return the directory of the executable (when frozen) or script."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def _resolve_model_path() -> str:
    """Locate hand_landmarker.task in PyInstaller bundle or app directory, downloading if missing."""
    model_name = 'hand_landmarker.task'
    bundle_dir = getattr(sys, '_MEIPASS', None)
    if bundle_dir:
        bundled_path = os.path.join(bundle_dir, model_name)
        if os.path.exists(bundled_path):
            return bundled_path

    # Ensure model path is relative to the script/executable directory, avoiding CWD issues
    model_path = os.path.join(_get_app_dir(), model_name)

    # Automatically download the model file if not found
    if not os.path.exists(model_path):
        print("Downloading hand_landmarker.task model...")
        url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
        urllib.request.urlretrieve(url, model_path)
        print("Model downloaded successfully.")

    return model_path


def _show_error(message: str) -> None:
    """Print an error message and show a Windows alert dialog when running as a frozen app."""
    print(message)
    if getattr(sys, 'frozen', False) and os.name == 'nt':
        ctypes.windll.user32.MessageBoxW(None, message, "Hand Gesture Brightness Control", 0x10)


MODEL_PATH = _resolve_model_path()

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionTaskRunningMode = mp.tasks.vision.RunningMode

with open(MODEL_PATH, 'rb') as model_file:
    model_data = model_file.read()

options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_buffer=model_data),
    running_mode=VisionTaskRunningMode.VIDEO,
    num_hands=1
)

landmarker = HandLandmarker.create_from_options(options)

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    _show_error("Error: Could not access webcam. Please ensure your camera is connected and permitted.")
    landmarker.close()
    sys.exit(1)

min_brightness = 0
max_brightness = 100

min_distance = 20
max_distance = 200

# Cache last set brightness to prevent WMI lag from setting brightness every single frame
last_brightness = -1

# Track start time to compute millisecond timestamps required by MediaPipe VIDEO mode
start_time_ms = cv2.getTickCount() / cv2.getTickFrequency() * 1000

print("Hand Gesture Brightness Control started! Press 'ESC' or close the window to exit.")

try:
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        # Milliseconds timestamp for VIDEO mode
        current_time_ms = cv2.getTickCount() / cv2.getTickFrequency() * 1000
        frame_timestamp_ms = int(current_time_ms - start_time_ms)

        # Detect Hands
        result = landmarker.detect_for_video(mp_image, frame_timestamp_ms)

        if result.hand_landmarks:
            for hand_landmark in result.hand_landmarks:
                h, w, _ = frame.shape

                # Landmark 4 = Thumb tip, Landmark 8 = Index finger tip
                x1 = int(hand_landmark[4].x * w)
                y1 = int(hand_landmark[4].y * h)

                x2 = int(hand_landmark[8].x * w)
                y2 = int(hand_landmark[8].y * h)

                cv2.circle(frame, (x1, y1), 10, (255, 26, 201), -1)
                cv2.circle(frame, (x2, y2), 10, (255, 26, 201), -1)
                cv2.line(frame, (x1, y1), (x2, y2), (255, 255, 255), 3)
                distance = np.hypot(x2 - x1, y2 - y1)

                # Convert distance to brightness
                brightness = int(np.interp(distance, [min_distance, max_distance],
                                           [min_brightness, max_brightness]))

                # Only change brightness when it differs by >= 2% to avoid WMI stutter
                if abs(brightness - last_brightness) >= 2:
                    try:
                        sbc.set_brightness(brightness)
                        last_brightness = brightness
                    except Exception:
                        pass

                cv2.putText(frame, f'Brightness: {brightness}%', (10, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        cv2.imshow('Brightness Control', frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC to quit
            break

        # Also exit if user closes the window with the 'X' button
        if cv2.getWindowProperty('Brightness Control', cv2.WND_PROP_VISIBLE) < 1:
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
    landmarker.close()
