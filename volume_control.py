"""volume_control.py
Gesture-driven smooth volume control.

Gestures
--------
  ☝  Index finger only       → Volume UP   (hold to keep raising)
  ✌  Index + Middle up       → Volume DOWN (hold to keep lowering)
  🤙  Thumb + Index + Pinky   → EXIT to Master Controller
  ESC / 'q'                  → Quit
"""

import cv2
import mediapipe as mp
import numpy as np
import time
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

print("Starting Volume Gesture Control...")

# ── Audio setup ──────────────────────────────────────────────────────────────
try:
    speakers  = AudioUtilities.GetSpeakers()
    interface = speakers.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume    = cast(interface, POINTER(IAudioEndpointVolume))
    print("Audio Initialized Successfully!")
except Exception as e:
    print("Audio Initialization Failed:", e)
    exit()

minVol, maxVol, _ = volume.GetVolumeRange()   # typically -65.25 to 0.0 dB

# ── Tuning ───────────────────────────────────────────────────────────────────
STEP_PER_SEC = 25.0   # % volume change per second while gesture is held

# ── MediaPipe ────────────────────────────────────────────────────────────────
mpHands = mp.solutions.hands
mpDraw  = mp.solutions.drawing_utils


# ── Helper ───────────────────────────────────────────────────────────────────
def finger_up(lm, tip, pip):
    """True if finger tip is above its PIP joint (finger extended)."""
    return lm[tip].y < lm[pip].y - 0.02


# ── Main callable ─────────────────────────────────────────────────────────────
def run_volume_control():
    """Called by master_gesture_controller to launch volume mode."""
    print("\n========== VOLUME CONTROL MODE ACTIVE ==========")
    print("  ☝  Index only          → Volume UP   (hold)")
    print("  ✌  Index + Middle      → Volume DOWN (hold)")
    print("  🤙 Thumb+Index+Pinky   → EXIT to Master")
    print("  ESC / Q                → Quit")
    print("=================================================\n")

    hands = mpHands.Hands(max_num_hands=1,
                          min_detection_confidence=0.7,
                          min_tracking_confidence=0.7)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Camera not detected!")
        return
    print("Camera Opened!")

    prev_time = time.time()

    while True:
        success, img = cap.read()
        if not success:
            continue

        now       = time.time()
        dt        = now - prev_time
        prev_time = now

        img = cv2.flip(img, 1)
        h, w, _ = img.shape
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        gesture = None   # 'up' | 'down' | None

        if results.multi_hand_landmarks:
            for handLms in results.multi_hand_landmarks:
                mpDraw.draw_landmarks(img, handLms, mpHands.HAND_CONNECTIONS)
                lm = handLms.landmark

                index_up  = finger_up(lm, 8,  6)
                middle_up = finger_up(lm, 12, 10)
                ring_up   = finger_up(lm, 16, 14)
                pinky_up  = finger_up(lm, 20, 18)
                thumb_up  = lm[4].x < lm[3].x

                # ── Master-exit: Thumb + Index + Pinky ──────────────
                if thumb_up and index_up and pinky_up and not middle_up and not ring_up:
                    print("EXIT GESTURE — returning to Master Controller...")
                    cap.release()
                    cv2.destroyAllWindows()
                    return

                # ✌ Index + Middle → volume DOWN  (more specific, check first)
                if index_up and middle_up and not ring_up and not pinky_up:
                    gesture = 'down'

                # ☝ Index only → volume UP
                elif index_up and not middle_up and not ring_up and not pinky_up:
                    gesture = 'up'

        # ── Apply smooth volume change ────────────────────────────────────────
        if gesture in ('up', 'down'):
            cur_vol_db = volume.GetMasterVolumeLevel()
            cur_pct    = np.interp(cur_vol_db, [minVol, maxVol], [0.0, 100.0])
            delta      = STEP_PER_SEC * dt
            new_pct    = cur_pct + delta if gesture == 'up' else cur_pct - delta
            new_pct    = max(0.0, min(100.0, new_pct))
            volume.SetMasterVolumeLevel(
                float(np.interp(new_pct, [0.0, 100.0], [minVol, maxVol])), None)

        # ── Current volume % for display ─────────────────────────────────────
        vol_pct = int(np.interp(volume.GetMasterVolumeLevel(),
                                [minVol, maxVol], [0, 100]))

        # ── Draw UI ──────────────────────────────────────────────────────────
        bar_x  = w - 60
        bar_h  = int(h * 0.6)
        bar_y0 = int(h * 0.2)
        bar_y1 = bar_y0 + bar_h
        filled = int(bar_h * vol_pct / 100)

        cv2.rectangle(img, (bar_x, bar_y0), (bar_x + 30, bar_y1), (50, 50, 50), -1)
        cv2.rectangle(img, (bar_x, bar_y1 - filled), (bar_x + 30, bar_y1),
                      (0, 200, 100) if gesture == 'up' else
                      (0, 100, 255) if gesture == 'down' else (0, 180, 80), -1)
        cv2.rectangle(img, (bar_x, bar_y0), (bar_x + 30, bar_y1), (200, 200, 200), 1)
        cv2.putText(img, f'{vol_pct}%', (bar_x - 5, bar_y0 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

        if gesture == 'up':
            label, colour = '  VOL UP  \u25b2', (0, 220, 100)
        elif gesture == 'down':
            label, colour = '  VOL DOWN \u25bc', (0, 120, 255)
        else:
            label, colour = 'Show Gesture', (180, 180, 180)

        cv2.putText(img, label, (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, colour, 3)
        cv2.putText(img, '\u261d=Vol Up | \u270c=Vol Down | T+I+Pinky=Exit | ESC=Quit',
                    (10, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)

        cv2.imshow("Gesture Volume Control", img)

        if cv2.waitKey(1) & 0xFF in (27, ord('q')):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Exiting Volume Control Mode...")


# ── Standalone entry point ────────────────────────────────────────────────────
if __name__ == "__main__":
    run_volume_control()