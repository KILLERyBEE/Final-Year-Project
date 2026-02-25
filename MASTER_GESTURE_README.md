# Master Gesture Controller - User Guide

## Overview

The **Master Gesture Controller** is a unified gesture-based application that manages multiple modes through hand gesture recognition. You can switch between different modes using specific hand gestures and control them with intuitive hand movements.

## Features

- **Multi-Mode Support**: Seamlessly switch between different gesture modes
- **Gesture-Based Navigation**: No keyboard required (except ESC to exit)
- **Real-time Hand Detection**: Uses MediaPipe for accurate hand tracking
- **Mode Switching**: Hold a gesture to confirm mode entry
- **Fist Exit**: Use fist gesture to exit any mode and return to detection mode

## Getting Started

### Prerequisites

Make sure you have these packages installed:
```bash
pip install opencv-python mediapipe pyautogui pillow pygetwindow
```

On Windows, you may also need:
```bash
pip install pywin32
```

### Running the Application

```bash
python master_gesture_controller.py
```

## Gesture Modes Guide

### 🎯 Detection Mode (Main Screen)

This is the main mode where you select which gesture mode to enter.

#### Available Gestures:

1. **👆 File Opening Mode**
   - Gesture: Thumb + Index finger up (other fingers down)
   - Hold the gesture for ~1 second to confirm entry
   - Use: Browse and open documents (Word, PPT, Excel, PDF)

2. **🤚 Scroll Mode**
   - Gesture: All fingers up (open palm)
   - Hold the gesture for ~1 second to confirm entry
   - Use: Scroll through documents and web pages

3. **☝️  Zoom Mode**
   - Gesture: Index finger only (other fingers down)
   - Hold the gesture for ~1 second to confirm entry
   - Use: Zoom in/out on documents

### 📁 File Opening Mode

Once in File Opening Mode, you can browse and open your files.

#### Gestures:
- **Pinch (Thumb + Index close together)**: Select a file type or file
  - Hold pinch for ~0.35 seconds to confirm selection
- **Back Gesture (Index + Middle fingers up)**: Go back to previous menu
  - Hold for ~0.3 seconds to execute
- **Fist (All fingers down)**: Close currently opened file
  - Hold for ~0.35 seconds

#### Navigation:
- Eye gaze/cursor follows your hand index finger
- Pinch on highlighted items to select them
- File types available: Word (.docx, .doc), PowerPoint (.pptx, .ppt), Excel (.xlsx, .xls), PDF (.pdf)

### 📜 Scroll Mode

Scroll through documents and web pages using different finger combinations.

#### Gestures:
- **☝️  Index Finger Only**: Scroll UP
- **✌️  Index + Middle Fingers**: Scroll DOWN
- **👍 Thumbs Up (Only thumb extended)**: FAST Scroll UP
- **🤚 Open Palm (All fingers up)**: FAST Scroll DOWN
- **✊ Fist (All fingers closed)**: EXIT back to detection mode

#### Behavior:
- Requires ~0.8 seconds cooldown between actions to prevent repeated scrolling
- Can be used in any application

### 🔍 Zoom Mode

Zoom in and out of documents using index and middle finger gestures.

#### Gestures:
- **☝️  Index Finger Only**: ZOOM IN
  - Hold for ~8 frames (changes detected)
- **✌️  Index + Middle Fingers**: ZOOM OUT
  - Hold for ~8 frames (changes detected)
- **✊ Fist (All fingers closed)**: EXIT back to detection mode
  - Hold for ~8 frames to confirm exit

#### Behavior:
- Works with Word, PowerPoint, Excel, PDF viewers
- Uses Ctrl+Scroll combination for zoom
- 0.5 seconds cooldown between zoom actions

## Example Usage Flows

### Flow 1: Open and Scroll a Document
1. Start application → See Detection Mode
2. Make "all fingers up" gesture and hold for 1 second
3. Enter Scroll Mode
4. Use index finger to scroll up, two fingers to scroll down
5. Make a fist and hold to exit
6. Return to Detection Mode

### Flow 2: Open Files and Zoom
1. Start application → See Detection Mode
2. Make "thumb + index up" gesture and hold for 1 second
3. Enter File Opening Mode
4. Pinch on "PDF" option to browse PDF files
5. Pinch on a PDF file to open it
6. Exit File Opening Mode (press ESC)
7. In Detection Mode, make "index only" gesture
8. Enter Zoom Mode
9. Use index finger to zoom in, index+middle to zoom out
10. Make a fist to exit
11. Return to Detection Mode

## Tips & Tricks

### Better Gesture Recognition:
- Keep your hand within a reasonable distance from the camera (20-80 cm recommended)
- Ensure good lighting for better hand detection
- Make clear, deliberate hand gestures
- Hold gestures steady when confirming mode entry

### Performance:
- The application uses ~2-5 MB RAM
- Requires a working webcam
- Process runs at ~30 FPS for real-time tracking

### Troubleshooting:
- **Hand not detected**: Ensure camera is working and settings allow camera access
- **Gesture not recognized**: Make sure you're using the exact finger position shown
- **Jumpy cursor**: Try improving lighting or adjusting camera angle
- **Slow scrolling**: Wait for cooldown period to pass before next gesture

## Exiting the Application

- From Detection Mode: Press **ESC** key
- From any Mode: Make a **Fist** gesture and hold to exit mode first, then press **ESC**

## Advanced Usage

### Customizing Gesture Confirmation Time
Edit the `master_gesture_controller.py` file:
```python
# In MasterGestureController.__init__()
self.CONFIRMATION_FRAMES = 10  # Change this value (higher = longer hold)
```

### Customizing Scroll Speed
Values are in the code:
```python
# In ScrollMode.run(): 
pyautogui.scroll(300)      # Normal scroll (positive = up, negative = down)
pyautogui.scroll(3000)     # Fast scroll
```

### Customizing Zoom Speed
```python
# In app_controller.py:
pyautogui.scroll(120)      # Change zooming speed
```

## File Structure

```
master_gesture_controller.py    # Main controller
├── ScrollMode              # Scroll gestures
├── ZoomMode                # Zoom gestures
├── FileOpeningMode         # File browser gestures
└── MasterGestureController # Main loop & detection

open_files.py              # File browser (not modified)
scroll.py                  # Original scroll (not modified)
Zoom.py                    # Original zoom (not modified)
app_controller.py          # System controls (not modified)
gesture_mouse_control.py   # Mouse control (not modified)
```

## Safety Notes

- ✅ Does not modify system files
- ✅ All hand gestures are safe and accessible
- ✅ Can be interrupted anytime with ESC
- ✅ Original code files are not modified
- ⚠️ Be careful with file selection - files will open in their default applications

## Feedback & Support

If you encounter any issues:
1. Check that all required packages are installed
2. Ensure camera is working properly
3. Try adjusting lighting
4. Test individual mode programs (scroll.py, Zoom.py, open_files.py) separately to isolate issues

## Version History

- **v1.0** (Initial): Master gesture controller with scroll, zoom, and file modes
  - File Opening Mode added
  - Scroll Mode refactored with cleaner gesture detection
  - Zoom Mode includes frame-based gesture confirmation
  - Detection Mode with visual feedback

---

**Enjoy hands-free gesture control! 👋**
