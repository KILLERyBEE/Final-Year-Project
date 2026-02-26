#complete
import cv2
import mediapipe as mp
import pyautogui
import time

# MediaPipe setup
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils


def fingers_up(hand):
    tips = [4, 8, 12, 16, 20]
    fingers = []

    # Thumb
    fingers.append(hand.landmark[tips[0]].x < hand.landmark[tips[0] - 1].x)

    # Other fingers
    for i in range(1, 5):
        fingers.append(hand.landmark[tips[i]].y < hand.landmark[tips[i] - 2].y)

    return fingers  # [thumb, index, middle, ring, pinky]


def run_slide_travel():
    """Run the slide travel (PPT gesture control) mode."""
    print("\n========== SLIDE TRAVEL MODE ACTIVE ==========")
    print("  ☝️  Index finger only          → NEXT SLIDE")
    print("  ✌️  Index + Middle             → PREVIOUS SLIDE")
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

    while True:
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                mp_draw.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
                )

                fingers = fingers_up(hand_landmarks)
                current_time = time.time()

                # Exit to master: Thumb + Index + Pinky up
                if fingers[0] and fingers[1] and fingers[4] and not fingers[2] and not fingers[3]:
                    print("EXIT GESTURE detected — returning to Master Controller...")
                    cap.release()
                    cv2.destroyAllWindows()
                    return

                # Cooldown to avoid multiple slide jumps
                if current_time - last_action_time > 1:

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

        cv2.imshow("PPT Gesture Control", frame)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC key
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Exiting Slide Travel Mode...")


# Allow running standalone for testing
if __name__ == "__main__":
    run_slide_travel()
