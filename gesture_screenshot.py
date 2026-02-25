import cv2
import mediapipe as mp
import pyautogui
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import time
import os

# Initialize MediaPipe Hand Detection
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)
mp_drawing = mp.solutions.drawing_utils

# Create screenshots folder if it doesn't exist
screenshot_folder = "screenshots"
if not os.path.exists(screenshot_folder):
    os.makedirs(screenshot_folder)

def are_fingers_up(hand_landmarks, handedness):
    """
    Check if pinky, index, and thumb are up
    Returns True if all three are extended
    """
    # Finger tip and pip indices
    THUMB_TIP = 4
    THUMB_IP = 3
    THUMB_MCP = 2
    
    INDEX_TIP = 8
    INDEX_PIP = 6
    
    PINKY_TIP = 20
    PINKY_PIP = 18
    
    landmarks = hand_landmarks.landmark
    
    # Check if thumb is up (extended)
    thumb_up = landmarks[THUMB_TIP].y < landmarks[THUMB_IP].y
    
    # Check if index is up (extended)
    index_up = landmarks[INDEX_TIP].y < landmarks[INDEX_PIP].y
    
    # Check if pinky is up (extended)
    pinky_up = landmarks[PINKY_TIP].y < landmarks[PINKY_PIP].y
    
    return thumb_up and index_up and pinky_up

def take_professional_screenshot():
    """
    Take a screenshot and add professional elements
    """
    try:
        # Take screenshot
        timestamp = datetime.now()
        screenshot = pyautogui.screenshot()
        
        # Add professional elements
        # Convert to PIL Image for editing
        img = screenshot.convert('RGB')
        draw = ImageDraw.Draw(img)
        
        # Add timestamp at bottom right
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        # Try to use a nice font, fallback to default
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        # Add semi-transparent background for timestamp
        text_bbox = draw.textbbox((0, 0), timestamp_str, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        padding = 10
        img_width, img_height = img.size
        
        # Draw background rectangle for timestamp
        x_pos = img_width - text_width - (padding * 2) - 10
        y_pos = img_height - text_height - (padding * 2) - 10
        
        draw.rectangle(
            [x_pos, y_pos, img_width - 10, img_height - 10],
            fill=(0, 0, 0),
            outline=(200, 200, 200)
        )
        
        # Draw timestamp text
        draw.text(
            (x_pos + padding, y_pos + padding),
            timestamp_str,
            font=font,
            fill=(255, 255, 255)
        )
        
        # Add a subtle watermark
        try:
            watermark_font = ImageFont.truetype("arial.ttf", 14)
        except:
            watermark_font = ImageFont.load_default()
        
        draw.text(
            (10, 10),
            "Gesture Screenshot",
            font=watermark_font,
            fill=(100, 100, 100)
        )
        
        # Save screenshot
        filename = timestamp.strftime("%Y%m%d_%H%M%S_screenshot.png")
        filepath = os.path.join(screenshot_folder, filename)
        img.save(filepath)
        
        print(f"✓ Professional screenshot saved: {filepath}")
        return True
    
    except Exception as e:
        print(f"Error taking screenshot: {e}")
        return False

def main():
    """
    Main function to run the gesture detection and screenshot program
    """
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    
    print("=" * 50)
    print("GESTURE SCREENSHOT PROGRAM")
    print("=" * 50)
    print("Instructions: Show pinky, index, and thumb (all up)")
    print("The gesture will trigger a 3-second countdown")
    print("Screenshot taken automatically after countdown completes")
    print("Press 'q' to quit")
    print("=" * 50)
    
    gesture_detected_time = None
    gesture_countdown_start = None
    screenshot_taken_time = None
    gesture_cooldown = 2  # 2 second cooldown between screenshots
    countdown_duration = 3  # 3 seconds to countdown before screenshot
    
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
        
        # Draw hand landmarks and check for gesture
        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                # Draw landmarks
                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                    mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2)
                )
                
                # Check if gesture is detected
                if are_fingers_up(hand_landmarks, handedness):
                    current_time = time.time()
                    
                    # Start countdown if gesture just detected
                    if gesture_countdown_start is None:
                        gesture_countdown_start = current_time
                        gesture_detected_time = current_time
                        print("Gesture detected! Countdown started...")
                    
                    # Calculate elapsed time since gesture detection
                    elapsed_time = current_time - gesture_countdown_start
                    remaining_time = max(0, countdown_duration - elapsed_time)
                    
                    # Display countdown
                    countdown_text = f"GESTURE DETECTED - Taking Screenshot in {remaining_time:.1f}s"
                    cv2.putText(
                        frame,
                        countdown_text,
                        (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1.2,
                        (0, 255, 0),
                        3
                    )
                    
                    # Large countdown number in center
                    countdown_number = f"{int(remaining_time) + 1 if remaining_time > 0 else 0}"
                    cv2.putText(
                        frame,
                        countdown_number,
                        (w // 2 - 40, h // 2 + 40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        3.5,
                        (0, 255, 0),
                        5
                    )
                    
                    # Check if countdown is complete
                    if elapsed_time >= countdown_duration:
                        # Take screenshot only if cooldown has passed
                        if screenshot_taken_time is None or (current_time - screenshot_taken_time) > gesture_cooldown:
                            cv2.putText(
                                frame,
                                "SCREENSHOT TAKEN!",
                                (50, 100),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                1.2,
                                (0, 0, 255),
                                3
                            )
                            take_professional_screenshot()
                            screenshot_taken_time = current_time
                            gesture_countdown_start = None  # Reset countdown
        else:
            # Reset countdown if hand is not detected
            gesture_countdown_start = None
        
        # Display instructions
        cv2.putText(frame, "Press 'q' to quit", (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
        
        # Show frame
        cv2.imshow("Gesture Screenshot - Show Pinky, Index & Thumb", frame)
        
        # Check for quit key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("\nProgram stopped by user")
            break
    
    cap.release()
    cv2.destroyAllWindows()
    hands.close()
    print(f"Screenshots saved in: {os.path.abspath(screenshot_folder)}")

if __name__ == "__main__":
    main()
