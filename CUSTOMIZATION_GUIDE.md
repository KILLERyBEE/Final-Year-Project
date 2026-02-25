# Configuration & Customization Guide

## 📝 Easy Customization

This guide shows you how to customize the Master Gesture Controller to match your preferences.

---

## ⚙️ Basic Configurations

### 1. Gesture Confirmation Time

**What it controls**: How long you need to hold a gesture to enter a mode in Detection Mode.

**Current setting**: ~0.3 seconds (10 frames @ 30 FPS)

**How to change**:
```python
# File: master_gesture_controller.py
# Find this line in MasterGestureController.__init__():

self.CONFIRMATION_FRAMES = 10  # ← Change this number

# Examples:
self.CONFIRMATION_FRAMES = 5   # Faster (sensitive)
self.CONFIRMATION_FRAMES = 15  # Slower (more deliberate)
```

---

## 📜 Scroll Mode Customization

### Scroll Speed

**What it controls**: How much the page scrolls with each gesture.

**Current settings**:
- Normal scroll: 300 pixels per action
- Fast scroll: 3000 pixels per action

**How to change**:
```python
# File: master_gesture_controller.py
# Find these lines in ScrollMode.run() method:

pyautogui.scroll(300)      # Line ~180 - normal scroll UP
pyautogui.scroll(-300)     # Line ~185 - normal scroll DOWN  
pyautogui.scroll(3000)     # Line ~193 - fast scroll UP
pyautogui.scroll(-3000)    # Line ~200 - fast scroll DOWN

# Change the numbers:
# Positive = scroll up
# Negative = scroll down
# Larger number = bigger scroll

# Example - make scrolling 2x faster:
pyautogui.scroll(600)      # Instead of 300
pyautogui.scroll(-600)     # Instead of -300
pyautogui.scroll(6000)     # Instead of 3000
pyautogui.scroll(-6000)    # Instead of -3000
```

### Scroll Cooldown

**What it controls**: How fast you can scroll repeatedly.

**Current setting**: 0.8 seconds between actions

**How to change**:
```python
# File: master_gesture_controller.py
# Find this line in ScrollMode.__init__():

self.last_action_time = time.time()

# And in ScrollMode.run() find:
if current_time - self.last_action_time > 0.8:  # ← This value

# Change 0.8 to your preference (in seconds):
if current_time - self.last_action_time > 0.5:  # Faster responses
if current_time - self.last_action_time > 1.2:  # More time between scrolls
```

---

## 🔍 Zoom Mode Customization

### Zoom Speed

**What it controls**: How much zoom is applied per gesture.

**Current setting**: 120 pixels (CtRL+Scroll)

**How to change**:
```python
# File: app_controller.py
# Find these functions:

def zoom_in():
    pyautogui.keyDown("ctrl")
    pyautogui.scroll(120)   # ← Change this number
    pyautogui.keyUp("ctrl")

def zoom_out():
    pyautogui.keyDown("ctrl")
    pyautogui.scroll(-120)  # ← Change this number
    pyautogui.keyUp("ctrl")

# Examples:
pyautogui.scroll(60)   # Slower zoom (finer control)
pyautogui.scroll(180)  # Faster zoom (bigger changes)
pyautogui.scroll(200)  # Very fast zoom
```

### Zoom Gesture Confirmation

**What it controls**: How long you need to hold a zoom gesture to trigger it.

**Current setting**: 8 frames @ 30 FPS ≈ 0.27 seconds

**How to change**:
```python
# File: master_gesture_controller.py
# Find in ZoomMode.__init__():

self.GESTURE_FRAMES_REQUIRED = 8  # ← Change this number

# More stable detection:
self.GESTURE_FRAMES_REQUIRED = 12  # Requires longer hold

# More responsive:
self.GESTURE_FRAMES_REQUIRED = 5   # Reacts faster
```

### Zoom Cooldown

**What it controls**: Minimum time between zoom actions.

**Current setting**: 0.5 seconds

**How to change**:
```python
# File: master_gesture_controller.py
# Find in ZoomMode.__init__():

self.ZOOM_COOLDOWN = 0.5  # ← Change this value

# For rapid zooming:
self.ZOOM_COOLDOWN = 0.2

# For controlled zooming:
self.ZOOM_COOLDOWN = 1.0
```

---

## 📁 File Opening Mode Customization

### Change Default Directory

**What it controls**: Where the file browser looks for files.

**Current**: Current working directory

**How to change**:
```python
# File: master_gesture_controller.py
# In MasterGestureController.enter_mode():

if mode_name == "file_mode":
    # Change this line:
    mode = FileOpeningMode()
    
    # To:
    mode = FileOpeningMode(root_dir="C:\\Users\\YourName\\Documents")
    mode.run()

# Or in open_files.py, modify HandFileOpener initialization
```

### Add More File Types

**What it controls**: Which file formats appear in the file browser.

**Current types**: Word, PPT, Excel, PDF

**How to change**:
```python
# File: open_files.py
# Find in HandFileOpener.__init__():

self.types = [
    ('Word', ('.docx', '.doc')),
    ('PPT', ('.pptx', '.ppt')),
    ('Excel', ('.xlsx', '.xls')),
    ('PDF', ('.pdf',))
]

# Add more types:
self.types = [
    ('Word', ('.docx', '.doc')),
    ('PPT', ('.pptx', '.ppt')),
    ('Excel', ('.xlsx', '.xls')),
    ('PDF', ('.pdf',)),
    ('Images', ('.jpg', '.png', '.bmp')),  # New
    ('Text', ('.txt', '.rtf')),             # New
]
```

### Adjust Pinch Sensitivity

**What it controls**: How close your fingers need to be to register as pinched.

**Current**: Dynamic based on hand size

**How to change**:
```python
# File: open_files.py
# Find in HandFileOpener.detect_pinch():

pinch_thresh = hand_size * 0.28  # ← Adjust multiplier

# Less sensitive (wider pinch needed):
pinch_thresh = hand_size * 0.35  # Requires tighter pinch

# More sensitive (wide pinch works):
pinch_thresh = hand_size * 0.20  # Easier to pinch
```

---

## 🎮 Hand Detection Customization

### Hand Detection Confidence

**What it controls**: How confident MediaPipe must be to detect a hand.

**Current**: 0.7 (70%)

**How to change**:
```python
# In each Mode class, find:

self.hands = self.mp_hands.Hands(
    min_detection_confidence=0.7,  # ← Change this
    min_tracking_confidence=0.7
)

# More strict (fewer false detections):
min_detection_confidence=0.85

# More lenient (detects hands easily):
min_detection_confidence=0.5
```

---

## 🎨 Visual Customization

### Change ON-Screen Text

**What it controls**: Displayed messages and instructions.

**How to change**:
```python
# Find any of these lines and modify:

cv2.putText(frame, "DETECTION MODE - Perform Gesture", ...)
cv2.putText(frame, "SCROLL MODE - Active", ...)
cv2.putText(frame, "Fist to EXIT", ...)

# Change the strings to your liking
```

### Change Colors

**What it controls**: RGB colors of text and overlays.

**Format**: BGR notation (0-255 each)

**How to change**:
```python
# Find lines with color tuples like:
cv2.putText(frame, text, pos, font, size, (0, 255, 0), thickness)
#                                            ↑ This is color (B, G, R)

# Common colors:
(0, 0, 255)      # Red
(0, 255, 0)      # Green
(255, 0, 0)      # Blue
(0, 255, 255)    # Yellow
(255, 0, 255)    # Magenta
(255, 255, 0)    # Cyan
(255, 255, 255)  # White
(0, 0, 0)        # Black
```

---

## 🔧 Advanced Customization

### Create Custom Gesture

**To add a new gesture pattern**:

1. **Identify finger pattern**:
```python
# Example: Pinky up only
[False, False, False, False, True]
```

2. **Add to gesture detection**:
```python
# In detect_mode_gesture():
if pinky and not any([thumb, index, middle, ring]):
    return "voice_mode"  # Example new mode
```

3. **Create mode class**:
```python
class VoiceMode:
    def __init__(self):
        pass
    
    def run(self):
        print("Voice mode activated!")
```

4. **Handle in enter_mode()**:
```python
elif mode_name == "voice_mode":
    mode = VoiceMode()
    mode.run()
```

### Modify Gesture Patterns

**Change existing gesture mapping in Detection Mode**:
```python
# File: master_gesture_controller.py
# In detect_mode_gesture() function:

def detect_mode_gesture(fingers):
    thumb, index, middle, ring, pinky = fingers
    
    # Current: thumb + index = file mode
    if thumb and index and not any([middle, ring, pinky]):
        return "file_mode"
    
    # Change to: thumb + index + middle = file mode
    if thumb and index and middle and not any([ring, pinky]):
        return "file_mode"
```

---

## 🧪 Testing Customizations

### Safe Testing Steps

1. **Backup original file**:
```bash
copy master_gesture_controller.py master_gesture_controller.bak
```

2. **Make one change at a time**

3. **Test the change**:
```bash
python master_gesture_controller.py
```

4. **If it breaks, restore**:
```bash
copy master_gesture_controller.bak master_gesture_controller.py
```

5. **If it works, keep the change**

---

## 📊 Configuration Presets

### Preset 1: "Sensitive" (For Beginners)
```python
# Detection: slower entry
CONFIRMATION_FRAMES = 15

# Scroll: slower movement
pyautogui.scroll(150)
pyautogui.scroll(-150)

# Zoom: more stable
GESTURE_FRAMES_REQUIRED = 12
ZOOM_COOLDOWN = 0.8

# Hand detection: lenient
min_detection_confidence=0.6
```

### Preset 2: "Responsive" (For Power Users)
```python
# Detection: fast entry
CONFIRMATION_FRAMES = 5

# Scroll: quick movement
pyautogui.scroll(500)
pyautogui.scroll(-500)

# Zoom: quick reactions
GESTURE_FRAMES_REQUIRED = 3
ZOOM_COOLDOWN = 0.2

# Hand detection: strict
min_detection_confidence=0.8
```

### Preset 3: "Balanced" (Recommended)
```python
# Detection: comfortable entry
CONFIRMATION_FRAMES = 10

# Scroll: medium movement
pyautogui.scroll(300)
pyautogui.scroll(-300)

# Zoom: stable
GESTURE_FRAMES_REQUIRED = 8
ZOOM_COOLDOWN = 0.5

# Hand detection: normal
min_detection_confidence=0.7
```

---

## ⚠️ Important Notes

- ✅ Always make backups before editing
- ✅ Test changes thoroughly
- ✅ Keep one working version
- ⚠️ Don't delete lines, only modify values
- ⚠️ Maintain proper Python indentation
- ⚠️ Don't break parentheses or quotes

---

## 🆘 If Something Breaks

1. **Check error message** for line number
2. **Restore from backup** if unsure
3. **Verify syntax** is correct
4. **Check indentation** matches original
5. **Reference original values** if confused

---

**Happy customizing! 🎉**
