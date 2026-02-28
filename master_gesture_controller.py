# Master Gesture Controller
# Main file to manage different gesture modes
import cv2
import mediapipe as mp
import pyautogui
import time
import numpy as np
from pathlib import Path

# Import mode classes and functions
from open_files import HandFileOpener
from app_controller import zoom_in, zoom_out
from scroll import run_scroll
from Zoom import run_zoom
from slidetravel import run_slide_travel
from gesture_screenshot import run_screenshot
from video_player import run_video_player

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# ==================== UTILITY FUNCTIONS ====================

def fingers_up(hand, h, w):
    """
    Detect which fingers are up based on hand landmarks.
    Returns: [thumb, index, middle, ring, pinky] as boolean list
    """
    lm = hand.landmark
    
    # Improved thumb detection - higher threshold reduces false positives
    thumb_tip = lm[4]
    thumb_pip = lm[2]
    # Thumb is extended if the horizontal offset from thumb PIP is significant
    thumb_extended = abs(thumb_tip.x - thumb_pip.x) > 0.06
    fingers = [thumb_extended]
    
    # Other fingers - check if tip is above PIP joint (extended)
    # Finger is up if tip.y < pip.y (tip is higher in frame)
    tip_ids = [8, 12, 16, 20]    # Index, Middle, Ring, Pinky tips
    pip_ids = [6, 10, 14, 18]    # Index, Middle, Ring, Pinky PIP joints
    
    for tip_id, pip_id in zip(tip_ids, pip_ids):
        tip = lm[tip_id]
        pip = lm[pip_id]
        # Finger is extended if tip is significantly above PIP
        is_extended = tip.y < (pip.y - 0.02)
        fingers.append(is_extended)
    
    return fingers


def detect_mode_gesture(fingers):
    """
    Detect gesture to enter a specific mode from detection mode.
    Returns the mode name or None.
    """
    thumb, index, middle, ring, pinky = fingers
    
    # Check in order from most specific to least specific
    
    # All fingers up = Scroll Mode (MOST SPECIFIC)
    if thumb and index and middle and ring and pinky:
        return "scroll_mode"
    
    # Thumb + Index up, others down = File Opening Mode
    if thumb and index and not middle and not ring and not pinky:
        return "file_mode"
    
    # Middle + Ring + Pinky up (no thumb/index) = Screenshot Mode
    if not thumb and not index and middle and ring and pinky:
        return "ss_mode"
    
    # Index + Middle fingers up (no thumb/ring/pinky) = Slide Travel Mode
    if not thumb and index and middle and not ring and not pinky:
        return "slide_mode"
    
    # Index + Middle + Ring up, no thumb, no pinky = Video Player Mode
    # (distinct from scroll=all5, slide=I+M, ss=M+R+P, zoom=I only)
    if not thumb and index and middle and ring and not pinky:
        return "video_mode"
    
    # Index only up, others down = Zoom Mode (LEAST SPECIFIC)
    if not thumb and index and not middle and not ring and not pinky:
        return "zoom_mode"
    
    return None


def is_fist(fingers):
    """Check if all fingers are closed (fist)"""
    return not any(fingers)


# ==================== SLIDESHOW AUTO-START HELPER ====================

def start_ppt_slideshow(wait=1.5):
    """Focus an open PowerPoint window and press F5 to start slideshow.
    
    Returns True if a PowerPoint window was found and F5 was sent.
    wait: seconds to wait after focusing before sending F5.
    """
    try:
        import pygetwindow as gw
        all_wins = gw.getAllWindows()
        # Look for any window whose title contains 'PowerPoint'
        ppt_wins = [w for w in all_wins
                    if 'powerpoint' in w.title.lower() or '.pptx' in w.title.lower()
                    or '.ppt' in w.title.lower()]
        if ppt_wins:
            win = ppt_wins[0]
            print(f"  [SlideMode] Found PPT window: '{win.title}'")
            try:
                win.activate()
            except Exception:
                pass
            time.sleep(wait)          # give PowerPoint time to focus
            pyautogui.press('f5')     # F5 = Start Slideshow from beginning
            time.sleep(0.5)
            print("  [SlideMode] Sent F5 → Slideshow started!")
            return True
        else:
            print("  [SlideMode] No open PowerPoint window found — start slideshow manually.")
            return False
    except ImportError:
        print("  [SlideMode] pygetwindow not installed — skipping auto-slideshow.")
        return False
    except Exception as e:
        print(f"  [SlideMode] Auto-slideshow error: {e}")
        return False


# Scroll and Zoom modes are provided by external modules:
# - Use `run_scroll()` from `scroll.py`
# - Use `run_zoom()` from `Zoom.py`
# These are imported at the top of this file and will be called
# by `enter_mode()` when the corresponding gesture is detected.


# ==================== FILE OPENING MODE ====================

class FileOpeningMode:
    def __init__(self, root_dir=None):
        self.file_opener = HandFileOpener(root_dir)
        self.mode_active = True

    def run(self):
        """Run file opening mode - uses existing HandFileOpener with exit message"""
        print("\n========== FILE OPENING MODE ACTIVE ==========")
        print("Use hand gestures to navigate and open files:")
        print("  • Pinch (thumb + index): Select item")
        print("  • Back gesture (index + middle): Go back")
        print("  • Press ESC to EXIT")
        print("=============================================\n")
        
        try:
            self.file_opener.run()
        except Exception as e:
            print(f"Error in file opening mode: {e}")
        
        cv2.destroyAllWindows()
        print("Exiting File Opening Mode...")


# ==================== MAIN GESTURE CONTROLLER ====================

class MasterGestureController:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.cap = cv2.VideoCapture(0)
        self.mode_confirmed = False
        self.confirmation_frames = 0
        self.CONFIRMATION_FRAMES = 10  # Frames to hold gesture to confirm mode entry

    def run(self):
        """Main loop - detection mode with gesture-based mode selection"""
        print("\n")
        print("==============================================")
        print("   MASTER GESTURE CONTROLLER - DETECTION MODE   ")
        print("==============================================")
        print("  Gesture Guide:                            ")
        print("  [1] Thumb + Index:     FILE OPENING MODE    ")
        print("  [2] All Fingers:       SCROLL MODE          ")
        print("  [3] Index Only:        ZOOM MODE            ")
        print("  [4] Index + Middle:    SLIDE TRAVEL MODE    ")
        print("  [5] Mid+Ring+Pinky:    SCREENSHOT MODE      ")
        print("  [6] Index+Middle+Ring (no Thumb/Pinky): VIDEO MODE ")
        print("  [7] Fist: EXIT from any mode               ")
        print("  Press ESC to quit application              ")
        print("==============================================\n")
        
        while True:
            try:
                success, frame = self.cap.read()
                if not success:
                    break
                
                frame = cv2.flip(frame, 1)
                h, w, _ = frame.shape
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                result = self.hands.process(rgb)
                
                # Display header
                cv2.rectangle(frame, (0, 0), (w, 100), (20, 20, 50), -1)
                cv2.putText(frame, "DETECTION MODE - Perform Gesture", (15, 35),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(frame, "T+I:File|All:Scroll|Idx:Zoom|I+M:Slide|M+R+P:SS", (15, 70),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255, 255, 255), 1)
                
                if result.multi_hand_landmarks:
                    for hand_landmarks in result.multi_hand_landmarks:
                        self.mp_draw.draw_landmarks(
                            frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS
                        )
                        
                        fingers = fingers_up(hand_landmarks, h, w)
                        gesture_mode = detect_mode_gesture(fingers)
                        
                        # Debug output
                        finger_str = f"[T:{int(fingers[0])}, I:{int(fingers[1])}, M:{int(fingers[2])}, R:{int(fingers[3])}, P:{int(fingers[4])}]"
                        
                        if gesture_mode:
                            self.confirmation_frames += 1
                            
                            # Display gesture being detected
                            mode_name = gesture_mode.replace("_", " ").upper()
                            cv2.putText(frame, f"Detected: {mode_name}", (15, h - 80),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                            cv2.putText(frame, f"Fingers: {finger_str}", (15, h - 110),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 255, 100), 1)
                            cv2.putText(frame, f"Hold to confirm: {self.confirmation_frames}/{self.CONFIRMATION_FRAMES}", 
                                       (15, h - 40),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)
                            
                            # Progress bar
                            bar_width = int((self.confirmation_frames / self.CONFIRMATION_FRAMES) * 300)
                            cv2.rectangle(frame, (15, h - 20), (15 + bar_width, h - 10), (0, 255, 0), -1)
                            cv2.rectangle(frame, (15, h - 20), (315, h - 10), (255, 255, 255), 2)
                            
                            # Enter mode if confirmation frames reached
                            if self.confirmation_frames >= self.CONFIRMATION_FRAMES:
                                print(f"\n>>> MODE SELECTED: {mode_name} <<<")
                                self.enter_mode(gesture_mode)
                                self.confirmation_frames = 0
                        else:
                            # Show what fingers are Up (for debugging)
                            cv2.putText(frame, f"Fingers: {finger_str}", (15, h - 40),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 200, 255), 1)
                            cv2.putText(frame, "Make a gesture to begin", (15, h - 80),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
                            self.confirmation_frames = 0
                else:
                    self.confirmation_frames = 0
                
                cv2.imshow("Master Gesture Controller", frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC key
                    print("\nExiting Master Gesture Controller...")
                    break
                    
            except Exception as e:
                print(f"Error in main loop: {e}")
                break
        
        self.cap.release()
        cv2.destroyAllWindows()

    def enter_mode(self, mode_name):
        """Enter the specified gesture mode"""
        self.cap.release()
        cv2.destroyAllWindows()
        time.sleep(0.5)
        
        try:
            if mode_name == "file_mode":
                print("\n>>> Entering FILE OPENING MODE <<<\n")
                # Use existing HandFileOpener.run()
                opener = HandFileOpener()
                opener.run()

            elif mode_name == "scroll_mode":
                print("\n>>> Entering SCROLL MODE <<<\n")
                # Delegate to scroll module
                run_scroll()

            elif mode_name == "zoom_mode":
                print("\n>>> Entering ZOOM MODE <<<\n")
                # Delegate to Zoom module
                run_zoom()

            elif mode_name == "slide_mode":
                print("\n>>> Entering SLIDE TRAVEL MODE <<<\n")
                # Auto-start slideshow if PowerPoint is already open
                start_ppt_slideshow(wait=1.5)
                # Delegate to slidetravel module
                run_slide_travel()

            elif mode_name == "ss_mode":
                print("\n>>> Entering SCREENSHOT MODE <<<\n")
                # Delegate to gesture_screenshot module
                run_screenshot()

            elif mode_name == "video_mode":
                print("\n>>> Entering VIDEO PLAYER MODE <<<\n")
                # Delegate to video_player module
                run_video_player()

        except Exception as e:
            print(f"Error running mode: {e}")
        
        # Reinitialize camera and detector for detection mode
        print("\n>>> Returning to DETECTION MODE <<<\n")
        self.cap = cv2.VideoCapture(0)
        time.sleep(1)
        # Reset confirmation frames to prevent accidental re-entry
        self.confirmation_frames = 0


# ==================== MAIN ENTRY POINT ====================

if __name__ == "__main__":
    controller = MasterGestureController()
    controller.run()
