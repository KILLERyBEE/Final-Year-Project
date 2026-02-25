import cv2
import mediapipe as mp
import pyautogui
import math
import time

# Initialize MediaPipe Hand Detection
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,  # Lower for more stable tracking
    min_tracking_confidence=0.3    # Lower for smoother continuous tracking
)
mp_drawing = mp.solutions.drawing_utils

# Get screen dimensions
screen_width, screen_height = pyautogui.size()

def distance_between_points(point1, point2):
    """Calculate Euclidean distance between two points"""
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def is_pinch_detected(hand_landmarks):
    """
    Detect if thumb and index finger are pinched together
    Returns True if distance between thumb tip and index tip is small
    """
    # Finger tip indices
    THUMB_TIP = 4
    INDEX_TIP = 8
    THUMB_IP = 3
    INDEX_PIP = 6
    
    landmarks = hand_landmarks.landmark
    
    # Get positions
    thumb_tip = (landmarks[THUMB_TIP].x, landmarks[THUMB_TIP].y)
    thumb_ip = (landmarks[THUMB_IP].x, landmarks[THUMB_IP].y)
    index_tip = (landmarks[INDEX_TIP].x, landmarks[INDEX_TIP].y)
    index_pip = (landmarks[INDEX_PIP].x, landmarks[INDEX_PIP].y)
    
    # Calculate distances (normalized 0-1 range)
    distance = distance_between_points(thumb_tip, index_tip)
    
    # Also check if both fingers are extended
    thumb_extended = landmarks[THUMB_TIP].y < landmarks[THUMB_IP].y
    index_extended = landmarks[INDEX_TIP].y < landmarks[INDEX_PIP].y
    
    # Pinch detected if distance is small AND both fingers are extended
    return distance < 0.06 and thumb_extended and index_extended

def get_index_finger_position(hand_landmarks, frame_width, frame_height):
    """
    Get the position of index finger tip
    Returns coordinates scaled to screen resolution with full screen coverage
    """
    INDEX_TIP = 8
    landmark = hand_landmarks.landmark[INDEX_TIP]
    
    # MediaPipe returns normalized coordinates (0-1 range)
    # x: 0 = left, 1 = right (already correct for mirrored camera view)
    # y: 0 = top, 1 = bottom
    
    # Use 1 - x for proper left-right mapping (camera is mirrored)
    normalized_x = 1.0 - landmark.x
    normalized_y = landmark.y
    
    # Clamp values to ensure they stay within 0-1 range
    normalized_x = max(0.0, min(1.0, normalized_x))
    normalized_y = max(0.0, min(1.0, normalized_y))
    
    # Direct mapping to screen coordinates with slight padding for edge detection
    screen_x = int(normalized_x * screen_width)
    screen_y = int(normalized_y * screen_height)
    
    # Ensure coordinates stay within screen bounds
    screen_x = max(0, min(screen_width - 1, screen_x))
    screen_y = max(0, min(screen_height - 1, screen_y))
    
    # Frame coordinates for visualization
    frame_x = frame_width - int(landmark.x * frame_width)
    frame_y = int(landmark.y * frame_height)
    
    return screen_x, screen_y, frame_x, frame_y

def draw_cursor(frame, x, y, is_pinching):
    """
    Draw custom cursor at the index finger position
    """
    cursor_radius = 15
    color = (0, 0, 255) if is_pinching else (0, 255, 0)  # Red if pinching, Green otherwise
    thickness = 3 if is_pinching else 2
    
    # Draw main circle
    cv2.circle(frame, (x, y), cursor_radius, color, thickness)
    
    # Draw crosshair
    line_length = 20
    cv2.line(frame, (x - line_length, y), (x + line_length, y), color, thickness)
    cv2.line(frame, (x, y - line_length), (x, y + line_length), color, thickness)
    
    # Draw center dot
    cv2.circle(frame, (x, y), 4, color, -1)
    
    # If pinching, draw additional indicators
    if is_pinching:
        cv2.circle(frame, (x, y), cursor_radius + 5, (0, 0, 255), 1)
        cv2.putText(
            frame,
            "PINCH DETECTED! CLICKING...",
            (x - 100, y - 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2
        )

def main():
    """
    Main function to run the gesture-based mouse control program
    """
    try:
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("Error: Could not open camera")
            return
        
        # Optimize camera settings for low latency
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer
        cap.set(cv2.CAP_PROP_FPS, 30)  # Set FPS to 30
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Lower resolution for faster processing
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Get frame dimensions
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print("=" * 60)
        print("GESTURE-BASED MOUSE CONTROL v3.0 - ULTRA SMOOTH")
        print("=" * 60)
        print("Instructions:")
        print("  • Move hand to control cursor position")
        print("  • Index finger = cursor position")
        print("  • Move finger to screen edges for full coverage")
        print("  • Pinch (thumb + index together) = LEFT CLICK")
        print("  • Press 'q' to quit")
        print("=" * 60)
        print(f"Screen Resolution: {screen_width}x{screen_height}")
        print(f"Camera Resolution: {frame_width}x{frame_height}")
        print(f"Smoothing: ULTRA SMOOTH (EMA + Velocity Tracking)")
        print(f"Detection Confidence: Optimized for stability")
        print("=" * 60)
        
        pinch_detected_last = False
        click_cooldown_time = None
        click_cooldown_duration = 0.5  # 0.5 second cooldown between clicks
        
        # Enhanced smoothing variables for ultra-smooth cursor movement
        prev_screen_x, prev_screen_y = screen_width // 2, screen_height // 2
        smoothing_factor = 0.75  # Much higher for smoother, continuous motion
        
        # Velocity tracking for predictive smoothing
        velocity_x, velocity_y = 0, 0
        velocity_factor = 0.3  # Smoothing for velocity
        
        while True:
            ret, frame = cap.read()
            
            if not ret:
                print("Error: Failed to read frame")
                break
            
            # Flip frame for selfie view
            frame = cv2.flip(frame, 1)
            h, w, c = frame.shape
            
            # Convert to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_frame)
            
            cursor_x, cursor_y = None, None
            is_pinching = False
            
            # Draw hand landmarks and detect gestures
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    try:
                        # Draw hand landmarks
                        mp_drawing.draw_landmarks(
                            frame,
                            hand_landmarks,
                            mp_hands.HAND_CONNECTIONS,
                            mp_drawing.DrawingSpec(color=(200, 100, 0), thickness=1, circle_radius=1),
                            mp_drawing.DrawingSpec(color=(200, 100, 0), thickness=1)
                        )
                        
                        # Get index finger position
                        screen_x, screen_y, frame_x, frame_y = get_index_finger_position(hand_landmarks, w, h)
                        
                        # Calculate velocity (for smoother motion)
                        vel_x = screen_x - prev_screen_x
                        vel_y = screen_y - prev_screen_y
                        
                        # Smooth the velocity
                        velocity_x = velocity_x * velocity_factor + vel_x * (1 - velocity_factor)
                        velocity_y = velocity_y * velocity_factor + vel_y * (1 - velocity_factor)
                        
                        # Apply exponential moving average smoothing (EMA)
                        smooth_screen_x = int(prev_screen_x * smoothing_factor + screen_x * (1 - smoothing_factor))
                        smooth_screen_y = int(prev_screen_y * smoothing_factor + screen_y * (1 - smoothing_factor))
                        
                        # Update previous position
                        prev_screen_x = smooth_screen_x
                        prev_screen_y = smooth_screen_y
                        
                        cursor_x, cursor_y = frame_x, frame_y
                        
                        # Move mouse to index finger position (with error handling)
                        try:
                            pyautogui.moveTo(smooth_screen_x, smooth_screen_y, duration=0)
                        except Exception as e:
                            pass  # Silently handle mouse positioning errors
                        
                        # Check if pinch is detected
                        is_pinching = is_pinch_detected(hand_landmarks)
                        
                        # Only click once per pinch (transition detection)
                        if is_pinching and not pinch_detected_last:
                            current_time = time.time()
                            
                            # Check cooldown before performing click
                            if click_cooldown_time is None or (current_time - click_cooldown_time) > click_cooldown_duration:
                                try:
                                    pyautogui.click()
                                    click_cooldown_time = current_time
                                    print(f"✓ LEFT CLICK performed at ({smooth_screen_x}, {smooth_screen_y})")
                                except Exception as e:
                                    pass  # Silently handle click errors
                        
                        # Update pinch state
                        pinch_detected_last = is_pinching
                    
                    except Exception as e:
                        print(f"Error processing hand landmarks: {e}")
                        continue
            else:
                # Reset pinch state if hand not detected
                pinch_detected_last = False
            
            # Draw cursor on frame
            if cursor_x is not None and cursor_y is not None:
                draw_cursor(frame, cursor_x, cursor_y, is_pinching)
            
            # Display screen position info
            cv2.putText(
                frame,
                f"Screen: {screen_width}x{screen_height}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )
            
            # Display smoothing info
            cv2.putText(
                frame,
                "Ultra Smooth EMA Tracking: ACTIVE",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 100),
                1
            )
            
            # Display current mode
            mode_text = "MODE: PINCHING" if is_pinching else "MODE: TRACKING"
            mode_color = (0, 0, 255) if is_pinching else (0, 255, 0)
            cv2.putText(
                frame,
                mode_text,
                (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                mode_color,
                2
            )
            
            # Draw screen area guide (corners)
            corner_size = 20
            cv2.line(frame, (0, 0), (corner_size, 0), (100, 100, 100), 2)  # Top-left
            cv2.line(frame, (0, 0), (0, corner_size), (100, 100, 100), 2)
            cv2.line(frame, (w-1, 0), (w-1-corner_size, 0), (100, 100, 100), 2)  # Top-right
            cv2.line(frame, (w-1, 0), (w-1, corner_size), (100, 100, 100), 2)
            cv2.line(frame, (0, h-1), (corner_size, h-1), (100, 100, 100), 2)  # Bottom-left
            cv2.line(frame, (0, h-1), (0, h-1-corner_size), (100, 100, 100), 2)
            cv2.line(frame, (w-1, h-1), (w-1-corner_size, h-1), (100, 100, 100), 2)  # Bottom-right
            cv2.line(frame, (w-1, h-1), (w-1, h-1-corner_size), (100, 100, 100), 2)
            
            # Instructions
            cv2.putText(
                frame,
                "Press 'q' to quit",
                (10, h - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (200, 200, 200),
                2
            )
            
            # Show frame
            cv2.imshow("Gesture Mouse Control - Index Finger Cursor & Pinch to Click", frame)
            
            # Check for quit key
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\nProgram stopped by user")
                break
        
        cap.release()
        cv2.destroyAllWindows()
        hands.close()
        print("Program closed successfully")
    
    except Exception as e:
        print(f"Fatal error: {e}")
        try:
            cap.release()
            cv2.destroyAllWindows()
            hands.close()
        except:
            pass

if __name__ == "__main__":
    main()
