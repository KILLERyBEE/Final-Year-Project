#complete
import cv2
import mediapipe as mp
import pyautogui
import time
import numpy as np

# MediaPipe setup
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

try:
    import pygetwindow as gw
except Exception:
    gw = None

try:
    import win32gui
    import win32con
except Exception:
    win32gui = None
    win32con = None

FIST_HOLD = 0.6   # seconds to hold fist to close PPT


def fingers_up(hand):
    tips = [4, 8, 12, 16, 20]
    fingers = []

    # Thumb
    fingers.append(hand.landmark[tips[0]].x < hand.landmark[tips[0] - 1].x)

    # Other fingers
    for i in range(1, 5):
        fingers.append(hand.landmark[tips[i]].y < hand.landmark[tips[i] - 2].y)

    return fingers  # [thumb, index, middle, ring, pinky]


def _is_fist(hand):
    """All four finger tips close to wrist → fist."""
    lm = hand.landmark
    wrist = np.array([lm[0].x, lm[0].y])
    tips = [8, 12, 16, 20]
    ref = max(0.01, np.hypot(lm[9].x - lm[0].x, lm[9].y - lm[0].y))
    avg = np.mean([np.hypot(lm[i].x - wrist[0], lm[i].y - wrist[1]) for i in tips])
    return avg < ref * 0.72


def _close_ppt():
    """Close any open PowerPoint window. Returns True if closed."""
    closed = False
    keywords = ('powerpoint', '.pptx', '.ppt')

    # Method 1: pygetwindow
    try:
        if gw:
            wins = [w for w in gw.getAllWindows()
                    if any(k in w.title.lower() for k in keywords)]
            for w in wins:
                try:
                    w.activate()
                    time.sleep(0.1)
                    w.close()
                    closed = True
                except Exception:
                    pass
    except Exception:
        pass

    # Method 2: win32gui WM_CLOSE
    if not closed:
        try:
            if win32gui and win32con:
                found = []
                def _cb(hwnd, extra):
                    txt = win32gui.GetWindowText(hwnd)
                    if txt and any(k in txt.lower() for k in keywords):
                        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                        extra.append(hwnd)
                win32gui.EnumWindows(_cb, found)
                closed = bool(found)
        except Exception:
            pass

    # Method 3: Escape first (exit slideshow), then Alt+F4
    if not closed:
        try:
            pyautogui.press('escape')   # exit slideshow → back to normal view
            time.sleep(0.3)
            pyautogui.hotkey('alt', 'f4')
            closed = True
        except Exception:
            pass

    return closed


def run_slide_travel():
    """Run the slide travel (PPT gesture control) mode."""
    print("\n========== SLIDE TRAVEL MODE ACTIVE ==========")
    print("  ☝️  Index finger only          → NEXT SLIDE")
    print("  ✌️  Index + Middle             → PREVIOUS SLIDE")
    print("  ✊  Fist (hold 0.6s)            → CLOSE PPT")
    print("  🤙  Thumb + Index + Pinky      → EXIT to Master")
    print("  Press ESC to EXIT")
    print("===============================================\n")

    hands = mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    )
    cap = cv2.VideoCapture(0)
    last_action_time = time.time()
    fist_start = None

    while True:
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        fist_detected = False

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                mp_draw.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
                )

                fingers = fingers_up(hand_landmarks)
                fist_detected = _is_fist(hand_landmarks)
                current_time = time.time()

                # ── Fist → close PPT ────────────────────────────────
                if fist_detected:
                    if fist_start is None:
                        fist_start = current_time
                    elapsed = current_time - fist_start
                    pct = min(1.0, elapsed / FIST_HOLD)
                    bar_w = int(pct * (w - 40))
                    cv2.rectangle(frame, (20, h - 40), (20 + bar_w, h - 25), (60, 60, 220), -1)
                    cv2.rectangle(frame, (20, h - 40), (w - 20,     h - 25), (255, 255, 255), 1)
                    cv2.putText(frame, f'CLOSING PPT... {int(pct*100)}%',
                                (24, h - 27), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (150, 150, 255), 1)
                    if elapsed >= FIST_HOLD:
                        print("FIST — closing PowerPoint...")
                        _close_ppt()
                        fist_start = None
                        last_action_time = current_time
                else:
                    fist_start = None

                # ── Exit to master gesture ───────────────────────────
                if fingers[0] and fingers[1] and fingers[4] and not fingers[2] and not fingers[3]:
                    print("EXIT GESTURE detected — returning to Master Controller...")
                    cap.release()
                    cv2.destroyAllWindows()
                    return

                # Cooldown to avoid multiple slide jumps
                if current_time - last_action_time > 1 and not fist_detected:

                    # ☝️ Index finger only → Next Slide
                    if fingers == [False, True, False, False, False]:
                        print("NEXT SLIDE")
                        pyautogui.press("right")
                        last_action_time = current_time

                    # ✌️ Index + Middle → Previous Slide
                    elif fingers == [False, True, True, False, False]:
                        print("PREVIOUS SLIDE")
                        pyautogui.press("left")
                        last_action_time = current_time

        else:
            fist_start = None  # reset if no hand visible

        # Hint overlay
        cv2.putText(frame, '☝=Next  ✌=Prev  Fist=ClosePPT  T+I+P=Exit',
                    (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

        cv2.imshow("PPT Gesture Control", frame)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC key
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Exiting Slide Travel Mode...")


# Allow running standalone for testing
if __name__ == "__main__":
    run_slide_travel()
