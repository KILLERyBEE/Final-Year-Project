import cv2
import mediapipe as mp
import pyautogui
import time

pyautogui.FAILSAFE = False

mp_hands = mp.solutions.hands
mp_draw  = mp.solutions.drawing_utils


def run_app_control():
    """Gesture-driven app switcher.

    Move index fingertip to the RIGHT edge → Alt+Tab (next app)
    Move index fingertip to the LEFT  edge → Alt+Shift+Tab (prev app)
    Thumb + Index + Pinky gesture          → exit back to master controller
    ESC key                                → quit
    """
    print("\n========== APP SWITCH MODE ACTIVE ==========")
    print("  ➡️  Index tip to RIGHT edge  → Next App   (Alt+Tab)")
    print("  ⬅️  Index tip to LEFT  edge  → Prev App   (Alt+Shift+Tab)")
    print("  🤙  Thumb + Index + Pinky    → EXIT to Master Controller")
    print("  Press ESC to quit")
    print("============================================\n")

    hands = mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    )
    cap = cv2.VideoCapture(0)

    last_switch = 0
    cooldown    = 1.2   # seconds between switches

    while True:
        success, img = cap.read()
        if not success:
            continue

        img = cv2.flip(img, 1)
        h, w, _ = img.shape

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)

        if results.multi_hand_landmarks:
            for handLms in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)

                lm = handLms.landmark
                x = int(lm[8].x * w)   # index fingertip x
                y = int(lm[8].y * h)

                cv2.circle(img, (x, y), 10, (0, 255, 0), cv2.FILLED)

                current_time = time.time()

                # ── Master-exit: Thumb + Index + Pinky ──────────────
                thumb_up  = lm[4].x < lm[3].x
                idx_up    = lm[8].y  < lm[6].y  - 0.02
                mid_up    = lm[12].y < lm[10].y - 0.02
                ring_up   = lm[16].y < lm[14].y - 0.02
                pinky_up  = lm[20].y < lm[18].y - 0.02

                if thumb_up and idx_up and pinky_up and not mid_up and not ring_up:
                    print("EXIT GESTURE — returning to Master Controller...")
                    cap.release()
                    cv2.destroyAllWindows()
                    return

                # ── App switching by index fingertip position ────────
                if current_time - last_switch > cooldown:
                    if x > w - 150:
                        pyautogui.hotkey('alt', 'tab')
                        last_switch = current_time
                        print("Next App →")

                    elif x < 150:
                        pyautogui.hotkey('alt', 'shift', 'tab')
                        last_switch = current_time
                        print("← Previous App")

        # Hint overlay
        cv2.putText(img, 'RIGHT=Next App | LEFT=Prev App | T+I+P=Exit',
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        # Edge zones visual guide
        cv2.rectangle(img, (0, 0),       (150, h),   (0, 80, 0),  1)
        cv2.rectangle(img, (w-150, 0),   (w, h),     (80, 0, 0),  1)
        cv2.putText(img, '< PREV', (5, h//2),     cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 0),  2)
        cv2.putText(img, 'NEXT >', (w-130, h//2), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 100, 255), 2)

        cv2.imshow("App Switch Gesture Control", img)

        if cv2.waitKey(1) & 0xFF in (27, ord('q')):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Exiting App Switch Mode...")


# Standalone run
if __name__ == "__main__":
    run_app_control()