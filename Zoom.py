import cv2
import mediapipe as mp
import time

from app_controller import zoom_in, zoom_out

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

# Add state tracking
zoom_mode_active = True
gesture_in_progress = False
current_gesture = None


def fingers_up(hand, h, w):
    """Improved finger detection with better thresholding"""
    lm = hand.landmark
    
    def P(i): 
        return int(lm[i].x * w), int(lm[i].y * h)
    
    # Improved thumb detection (more robust)
    thumb_tip = lm[4]
    thumb_ip = lm[3]
    thumb_mcp = lm[2]
    
    # Check if thumb is extended (to the side)
    thumb_extended = thumb_tip.x < thumb_ip.x
    
    fingers = [thumb_extended]
    
    # Finger tip joints
    tip_ids = [8, 12, 16, 20]
    pip_ids = [6, 10, 14, 18]
    
    for tip_id, pip_id in zip(tip_ids, pip_ids):
        tip = lm[tip_id]
        pip = lm[pip_id]
        # More robust finger detection with better threshold
        if tip_id == 8:  # Index finger
            # Index finger needs to be more extended for zoom
            fingers.append(tip.y < pip.y - 0.02)
        else:
            fingers.append(tip.y < pip.y)
    
    return fingers


def detect_gesture(fingers):
    """Detect specific gestures from finger states"""
    thumb, index, middle, ring, pinky = fingers
    
    # Index finger only (zoom in)
    if index and not any([middle, ring, pinky]):
        # Thumb can be either up or down for zoom in
        return "zoom_in"
    
    # Index and middle fingers only (zoom out)
    elif index and middle and not any([ring, pinky]):
        # Thumb can be either up or down for zoom out
        return "zoom_out"
    
    # Fist (all fingers down)
    elif not any([thumb, index, middle, ring, pinky]):
        return "fist"
    
    return None


with mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
) as hands:
    
    print("Starting Zoom Mode...")
    print("Gestures:")
    print("- Index finger only: Zoom In")
    print("- Index + Middle fingers: Zoom Out")
    print("- Fist: Exit")
    
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
            
            # Reset counters for other gestures when a new gesture is detected
            if gesture != current_gesture:
                zoom_in_frames = 0
                zoom_out_frames = 0
                fist_frames = 0
                current_gesture = gesture
            
            # Accumulate frames for the current gesture
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
                # Reset all if no clear gesture
                zoom_in_frames = 0
                zoom_out_frames = 0
                fist_frames = 0
                current_gesture = None
            
            # Check if gesture is held long enough and cooldown has passed
            if (current_time - last_action_time) >= ZOOM_COOLDOWN:
                if zoom_in_frames >= GESTURE_FRAMES_REQUIRED:
                    zoom_in()
                    print(f"ZOOM IN - Gesture held for {zoom_in_frames} frames")
                    last_action_time = current_time
                    # Reset after action to require new gesture
                    zoom_in_frames = 0
                    current_gesture = None
                
                elif zoom_out_frames >= GESTURE_FRAMES_REQUIRED:
                    zoom_out()
                    print(f"ZOOM OUT - Gesture held for {zoom_out_frames} frames")
                    last_action_time = current_time
                    # Reset after action to require new gesture
                    zoom_out_frames = 0
                    current_gesture = None
            
            # Check for fist to exit
            if fist_frames >= GESTURE_FRAMES_REQUIRED:
                print("Exiting Zoom Mode...")
                zoom_mode_active = False
                break
            
            # Display current gesture status
            if current_gesture:
                cv2.putText(frame, f"Gesture: {current_gesture.upper()}", 
                           (10, h - 60), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.7, (0, 255, 0), 2)
                cv2.putText(frame, f"Frames: {max(zoom_in_frames, zoom_out_frames, fist_frames)}/{GESTURE_FRAMES_REQUIRED}", 
                           (10, h - 30), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.5, (255, 255, 255), 2)
        
        else:
            # Reset counters when no hand is detected
            zoom_in_frames = 0
            zoom_out_frames = 0
            fist_frames = 0
            current_gesture = None
        
        # Display mode info
        cv2.putText(frame, "ZOOM MODE - ACTIVE", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Display cooldown status
        time_since_last_action = current_time - last_action_time
        if time_since_last_action < ZOOM_COOLDOWN:
            cooldown_percent = time_since_last_action / ZOOM_COOLDOWN
            bar_width = int(200 * cooldown_percent)
            cv2.rectangle(frame, (10, h - 100), (10 + bar_width, h - 90), 
                         (0, 255, 0), -1)
            cv2.rectangle(frame, (10, h - 100), (210, h - 90), 
                         (255, 255, 255), 1)
            cv2.putText(frame, "Cooldown", (10, h - 105), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        cv2.imshow("ZOOM MODE", frame)
        
        # Exit on ESC key
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC key
            print("Exiting by user request...")
            break

cap.release()
cv2.destroyAllWindows()
print("Zoom mode ended.")