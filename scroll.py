#"""Scroll mode runner usable as module or script."""
import cv2
import mediapipe as mp
import pyautogui
import time


def run_scroll():
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(max_num_hands=1,
                           min_detection_confidence=0.7,
                           min_tracking_confidence=0.7)
    mp_draw = mp.solutions.drawing_utils

    cap = cv2.VideoCapture(0)
    last_action_time = time.time()

    def fingers_up(hand):
        tips = [4, 8, 12, 16, 20]
        fingers = []

        # Thumb
        fingers.append(hand.landmark[tips[0]].x < hand.landmark[tips[0]-1].x)

        # Other fingers
        for i in range(1, 5):
            fingers.append(hand.landmark[tips[i]].y < hand.landmark[tips[i]-2].y)

        return fingers  # [thumb, index, middle, ring, pinky]

    print("\n========== SCROLL MODE ACTIVE ==========")
    exit_start = None
    EXIT_HOLD = 2.0  # seconds required to return to master controller
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

                # Check for master-exit gesture: Thumb + Index + Pinky up (others down)
                # fingers = [thumb, index, middle, ring, pinky]
                if fingers[0] and fingers[1] and (not fingers[2]) and (not fingers[3]) and fingers[4]:
                    if exit_start is None:
                        exit_start = current_time
                    elif current_time - exit_start >= EXIT_HOLD:
                        print("Master-exit gesture held — returning to master controller...")
                        cap.release()
                        cv2.destroyAllWindows()
                        return
                else:
                    exit_start = None

                # Cooldown to avoid repeated triggers
                if current_time - last_action_time > 0.8:

                    # Fist (no action)
                    if fingers == [False, False, False, False, False]:
                        last_action_time = current_time

                    # Index finger → Scroll UP (normal)
                    elif fingers == [False, True, False, False, False]:
                        pyautogui.scroll(300)
                        last_action_time = current_time

                    # Two fingers → Scroll DOWN (normal)
                    elif fingers == [False, True, True, False, False]:
                        pyautogui.scroll(-300)
                        last_action_time = current_time

                    # Thumbs up → FAST Scroll UP
                    elif fingers == [True, False, False, False, False]:
                        pyautogui.scroll(3000)
                        last_action_time = current_time

                    # Open Palm → FAST Scroll DOWN
                    elif fingers == [True, True, True, True, True]:
                        pyautogui.scroll(-3000)
                        last_action_time = current_time

        cv2.imshow("Gesture Control - Scroll Mode", frame)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    run_scroll()
