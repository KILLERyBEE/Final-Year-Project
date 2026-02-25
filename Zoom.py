import cv2
import mediapipe as mp
import time

from app_controller import zoom_in, zoom_out


def run_zoom():
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils

    cap = cv2.VideoCapture(0)

    # Reset gesture counters
    zoom_in_frames = 0
    zoom_out_frames = 0
    fist_frames = 0

    GESTURE_FRAMES_REQUIRED = 8  # Increased for more stability
    ZOOM_COOLDOWN = 0.5  # Increased cooldown to prevent rapid firing
    last_action_time = 0

    zoom_mode_active = True
    current_gesture = None

    def fingers_up(hand, h, w):
        lm = hand.landmark
        thumb_tip = lm[4]
        thumb_ip = lm[3]
        thumb_extended = thumb_tip.x < thumb_ip.x
        fingers = [thumb_extended]
        tip_ids = [8, 12, 16, 20]
        pip_ids = [6, 10, 14, 18]
        for tip_id, pip_id in zip(tip_ids, pip_ids):
            tip = lm[tip_id]
            pip = lm[pip_id]
            if tip_id == 8:
                fingers.append(tip.y < pip.y - 0.02)
            else:
                fingers.append(tip.y < pip.y)
        return fingers

    def detect_gesture(fingers):
        thumb, index, middle, ring, pinky = fingers
        if index and not any([middle, ring, pinky]):
            return "zoom_in"
        elif index and middle and not any([ring, pinky]):
            return "zoom_out"
        elif not any([thumb, index, middle, ring, pinky]):
            return "fist"
        return None

    with mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    ) as hands:
        print("Starting Zoom Mode...")
        print("Gestures: Index -> Zoom In; Index+Middle -> Zoom Out; Fist -> Exit")
        exit_start = None
        EXIT_HOLD = 2.0  # seconds required to return to master controller

        while zoom_mode_active:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = hands.process(rgb)

            current_time = time.time()

            if result.multi_hand_landmarks:
                hand = result.multi_hand_landmarks[0]
                mp_drawing.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

                fingers = fingers_up(hand, h, w)
                gesture = detect_gesture(fingers)

                # Check for master-exit gesture: Thumb + Index + Pinky up (others down)
                # fingers = [thumb, index, middle, ring, pinky]
                if fingers[0] and fingers[1] and (not fingers[2]) and (not fingers[3]) and fingers[4]:
                    if exit_start is None:
                        exit_start = current_time
                    elif current_time - exit_start >= EXIT_HOLD:
                        print("Master-exit gesture held — returning to master controller...")
                        break
                else:
                    exit_start = None

                # Use local counters captured by closure via mutable types
                if gesture != current_gesture:
                    zoom_in_frames = 0
                    zoom_out_frames = 0
                    fist_frames = 0
                    current_gesture = gesture

                if gesture == "zoom_in":
                    zoom_in_frames += 1
                    zoom_out_frames = 0
                    fist_frames = 0
                elif gesture == "zoom_out":
                    zoom_out_frames += 1
                    zoom_in_frames = 0
                    fist_frames = 0
                elif gesture == "fist":
                    fist_frames += 1
                    zoom_in_frames = 0
                    zoom_out_frames = 0
                else:
                    zoom_in_frames = 0
                    zoom_out_frames = 0
                    fist_frames = 0
                    current_gesture = None

                if (current_time - last_action_time) >= ZOOM_COOLDOWN:
                    if zoom_in_frames >= GESTURE_FRAMES_REQUIRED:
                        zoom_in()
                        print(f"ZOOM IN - Gesture held for {zoom_in_frames} frames")
                        last_action_time = current_time
                        zoom_in_frames = 0
                        current_gesture = None
                    elif zoom_out_frames >= GESTURE_FRAMES_REQUIRED:
                        zoom_out()
                        print(f"ZOOM OUT - Gesture held for {zoom_out_frames} frames")
                        last_action_time = current_time
                        zoom_out_frames = 0
                        current_gesture = None

                if fist_frames >= GESTURE_FRAMES_REQUIRED:
                    print("Exiting Zoom Mode...")
                    break

            else:
                zoom_in_frames = 0
                zoom_out_frames = 0
                fist_frames = 0
                current_gesture = None

            cv2.putText(frame, "ZOOM MODE - ACTIVE", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, "Fist to EXIT", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            cv2.imshow("Gesture Control - Zoom Mode", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 27:
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    run_zoom()