
#Docstring for volume
import cv2
import mediapipe as mp
import numpy as np
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import math

# -----------------------------
# Initialize Windows Volume Control
# -----------------------------
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))

volRange = volume.GetVolumeRange()
minVol = volRange[0]
maxVol = volRange[1]

# -----------------------------
# Mediapipe Setup
# -----------------------------
mpHands = mp.solutions.hands
hands = mpHands.Hands(max_num_hands=1)
mpDraw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

while True:
    success, img = cap.read()
    if not success:
        break

    img = cv2.flip(img, 1)
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            lmList = []
            for id, lm in enumerate(handLms.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                lmList.append((id, cx, cy))

            mpDraw.draw_landmarks(img, handLms, mpHands.HAND_CONNECTIONS)

            # Thumb tip = id 4
            # Index tip = id 8
            x1, y1 = lmList[4][1], lmList[4][2]
            x2, y2 = lmList[8][1], lmList[8][2]

            # Draw circles
            cv2.circle(img, (x1, y1), 10, (255, 0, 0), cv2.FILLED)
            cv2.circle(img, (x2, y2), 10, (255, 0, 0), cv2.FILLED)
            cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 3)

            # Calculate distance
            length = math.hypot(x2 - x1, y2 - y1)

            # Convert distance to volume range
            vol = np.interp(length, [30, 200], [minVol, maxVol])
            volume.SetMasterVolumeLevel(vol, None)

            # Volume percentage display
            volPercent = np.interp(length, [30, 200], [0, 100])

            cv2.putText(img, f'Volume: {int(volPercent)} %',
                        (40, 50), cv2.FONT_HERSHEY_SIMPLEX,
                        1, (0, 255, 0), 3)

    cv2.imshow("Gesture Volume Control", img)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()


'''
import cv2
import mediapipe as mp
import numpy as np
import math
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

print("Starting Volume Gesture Control...")

# -----------------------------
# STABLE AUDIO INITIALIZATION
# -----------------------------
try:
    speakers = AudioUtilities.GetSpeakers()
    interface = speakers.Activate(
        IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    print("Audio Initialized Successfully!")
except Exception as e:
    print("Audio Initialization Failed:", e)
    exit()

minVol, maxVol, _ = volume.GetVolumeRange()

# -----------------------------
# Mediapipe Setup
# -----------------------------
mpHands = mp.solutions.hands
hands = mpHands.Hands(max_num_hands=1)
mpDraw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("Camera not detected!")
    exit()

print("Camera Opened!")

while True:
    success, img = cap.read()
    if not success:
        break

    img = cv2.flip(img, 1)
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            lmList = []
            for id, lm in enumerate(handLms.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                lmList.append((id, cx, cy))

            mpDraw.draw_landmarks(img, handLms, mpHands.HAND_CONNECTIONS)

            x1, y1 = lmList[4][1], lmList[4][2]
            x2, y2 = lmList[8][1], lmList[8][2]

            cv2.circle(img, (x1, y1), 10, (255, 0, 0), cv2.FILLED)
            cv2.circle(img, (x2, y2), 10, (255, 0, 0), cv2.FILLED)
            cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 3)
            
            # Get thumb and index tip
            x1, y1 = lmList[4][1], lmList[4][2]
            x2, y2 = lmList[8][1], lmList[8][2]

            # Midpoint
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            cv2.circle(img, (cx, cy), 8, (255, 0, 255), cv2.FILLED)

            # Calculate pinch distance
            length = math.hypot(x2 - x1, y2 - y1)

            # Activate only when fingers are pinched
            if length < 40:

                if 'prevY' not in globals() or prevY is None:
                    prevY = cy

                diff = prevY - cy  # upward movement increases volume

                sensitivity = 0.5  # adjust this if needed

                currentVol = volume.GetMasterVolumeLevel()
                newVol = currentVol + diff * sensitivity

                # Clamp volume safely
                newVol = max(minVol, min(maxVol, newVol))

                volume.SetMasterVolumeLevel(newVol, None)

                prevY = cy

            else:
                prevY = None  # Reset when pinch released

            # Always show actual system volume
            currentVol = volume.GetMasterVolumeLevel()
            volPercent = np.interp(currentVol, [minVol, maxVol], [0, 100])

            cv2.putText(img, f'Volume: {int(volPercent)} %',
                        (40, 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        3)

    cv2.imshow("Gesture Volume Control", img)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
'''