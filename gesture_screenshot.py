import cv2
import mediapipe as mp
import pyautogui
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import time
import os

# Initialize MediaPipe Hand Detection
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Create screenshots folder if it doesn't exist
screenshot_folder = "screenshots"
if not os.path.exists(screenshot_folder):
    os.makedirs(screenshot_folder)


def are_fingers_up(hand_landmarks):
    """
    Screenshot trigger: Index finger only up, all others down.
    """
    tips = [4, 8, 12, 16, 20]
    lm = hand_landmarks.landmark

    fingers = []
    # Thumb: compare x
    fingers.append(lm[tips[0]].x < lm[tips[0] - 1].x)
    # Other fingers: tip above PIP
    for i in range(1, 5):
        fingers.append(lm[tips[i]].y < lm[tips[i] - 2].y)

    # Index only: [F, T, F, F, F]
    return fingers == [False, True, False, False, False]


def is_exit_gesture(hand_landmarks):
    """
    Exit-to-master gesture: Thumb + Index + Pinky up, Middle + Ring down.
    [thumb=T, index=T, middle=F, ring=F, pinky=T]
    """
    lm = hand_landmarks.landmark

    tips = [4, 8, 12, 16, 20]
    fingers = []

    # Thumb: compare x positions
    fingers.append(lm[tips[0]].x < lm[tips[0] - 1].x)

    # Other fingers: tip above PIP
    for i in range(1, 5):
        fingers.append(lm[tips[i]].y < lm[tips[i] - 2].y)

    thumb, index, middle, ring, pinky = fingers
    return thumb and index and not middle and not ring and pinky


def take_professional_screenshot():
    """Take a screenshot and add professional timestamp/watermark."""
    try:
        timestamp = datetime.now()
        screenshot = pyautogui.screenshot()

        img = screenshot.convert('RGB')
        draw = ImageDraw.Draw(img)

        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()

        text_bbox = draw.textbbox((0, 0), timestamp_str, font=font)
        text_width  = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        padding = 10
        img_width, img_height = img.size

        x_pos = img_width  - text_width  - (padding * 2) - 10
        y_pos = img_height - text_height - (padding * 2) - 10

        draw.rectangle(
            [x_pos, y_pos, img_width - 10, img_height - 10],
            fill=(0, 0, 0),
            outline=(200, 200, 200)
        )
        draw.text(
            (x_pos + padding, y_pos + padding),
            timestamp_str, font=font, fill=(255, 255, 255)
        )

        try:
            wm_font = ImageFont.truetype("arial.ttf", 14)
        except:
            wm_font = ImageFont.load_default()

        draw.text((10, 10), "Gesture Screenshot", font=wm_font, fill=(100, 100, 100))

        filename = timestamp.strftime("%Y%m%d_%H%M%S_screenshot.png")
        filepath = os.path.join(screenshot_folder, filename)
        img.save(filepath)

        print(f"✓ Screenshot saved: {filepath}")
        return True

    except Exception as e:
        print(f"Error taking screenshot: {e}")
        return False


def run_screenshot():
    """Run the gesture screenshot mode — callable from master controller."""
    print("\n========== SCREENSHOT MODE ACTIVE ==========")
    print("  ☝️  Index finger only       → TAKE SCREENSHOT (hold 3s)")
    print("  🤙  Thumb + Index + Pinky   → EXIT to Master  (hold 2s)")
    print("  Press ESC to EXIT")
    print("=============================================\n")

    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    )
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open camera")
        hands.close()
        return

    gesture_countdown_start = None
    screenshot_taken_time   = None
    exit_start              = None

    GESTURE_COOLDOWN   = 2.0   # seconds between screenshots
    COUNTDOWN_DURATION = 3.0   # seconds before snap
    EXIT_HOLD          = 2.0   # seconds to hold exit gesture

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to read frame")
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        current_time = time.time()

        # Header bar
        cv2.rectangle(frame, (0, 0), (w, 70), (20, 20, 50), -1)
        cv2.putText(frame, "SCREENSHOT MODE", (15, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, "Index Only (3s): Snap | T+I+Pinky (2s): Exit | ESC: Quit",
                    (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]

            # Draw landmarks
            mp_drawing.draw_landmarks(
                frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2)
            )

            # --- Exit-to-master gesture check (thumb + index + pinky, hold 2s) ---
            if is_exit_gesture(hand_landmarks):
                if exit_start is None:
                    exit_start = current_time
                held = current_time - exit_start
                remaining = max(0.0, EXIT_HOLD - held)
                cv2.putText(frame, f"EXIT in {remaining:.1f}s — Keep holding!", (15, h - 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 100, 255), 2)
                if held >= EXIT_HOLD:
                    print("EXIT GESTURE held — returning to Master Controller...")
                    break
            else:
                exit_start = None

            # --- Screenshot trigger gesture ---
            if are_fingers_up(hand_landmarks):
                if gesture_countdown_start is None:
                    gesture_countdown_start = current_time
                    print("Gesture detected! Countdown started...")

                elapsed   = current_time - gesture_countdown_start
                remaining = max(0.0, COUNTDOWN_DURATION - elapsed)

                cv2.putText(frame, f"☝️ SCREENSHOT in {remaining:.1f}s", (15, h - 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
                cv2.putText(frame, str(int(remaining) + 1 if remaining > 0 else 0),
                            (w // 2 - 30, h // 2 + 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 3.5, (0, 255, 0), 5)

                if elapsed >= COUNTDOWN_DURATION:
                    if screenshot_taken_time is None or (current_time - screenshot_taken_time) > GESTURE_COOLDOWN:
                        cv2.putText(frame, "SCREENSHOT TAKEN!", (50, 120),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
                        take_professional_screenshot()
                        screenshot_taken_time = current_time
                    gesture_countdown_start = None
            else:
                gesture_countdown_start = None

        else:
            gesture_countdown_start = None
            exit_start = None
            cv2.putText(frame, "No hand detected", (15, h - 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 150), 1)

        cv2.imshow("Gesture Screenshot", frame)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()
    hands.close()
    print("Exiting Screenshot Mode...")


# Allow running standalone for testing
if __name__ == "__main__":
    run_screenshot()
