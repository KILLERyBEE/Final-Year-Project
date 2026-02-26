import cv2
import mediapipe as mp
import pyautogui
import time

pyautogui.FAILSAFE = False

# Initialize MediaPipe Hand Landmarker
BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path='hand_landmarker.task'),
    running_mode=VisionRunningMode.IMAGE,
    num_hands=1,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.7
)

detector = HandLandmarker.create_from_options(options)

cap = cv2.VideoCapture(0)

last_switch = 0
cooldown = 1.2

while True:
    success, img = cap.read()
    if not success:
        continue

    img = cv2.flip(img, 1)
    h, w, _ = img.shape

    # Convert to MediaPipe Image format
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img)

    # Detect hand landmarks
    results = detector.detect(mp_image)

    if results.hand_landmarks:
        for hand_landmarks in results.hand_landmarks:
            # Draw landmarks
            mp.tasks.vision.draw_landmarks(
                img,
                hand_landmarks,
                mp.tasks.vision.HandLandmarksConnections.HAND_CONNECTIONS,
                mp.tasks.vision.drawing_styles.get_default_hand_landmarks_style(),
                mp.tasks.vision.drawing_styles.get_default_hand_connections_style()
            )

            # Get index finger tip coordinates
            index_finger_tip = hand_landmarks[8]  # Index finger tip landmark
            x = int(index_finger_tip.x * w)
            y = int(index_finger_tip.y * h)

            cv2.circle(img, (x, y), 10, (0, 255, 0), cv2.FILLED)

            current_time = time.time()

            if current_time - last_switch > cooldown:

                if x > w - 150:
                    pyautogui.hotkey('alt', 'tab')
                    last_switch = current_time
                    print("Next App")

                elif x < 150:
                    pyautogui.hotkey('alt', 'shift', 'tab')
                    last_switch = current_time
                    print("Previous App")

    cv2.imshow("App Switch Gesture Control", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
detector.close()