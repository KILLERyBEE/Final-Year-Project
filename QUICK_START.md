# Quick Start Guide - Master Gesture Controller

## 🚀 Quick Setup (2 minutes)

### Step 1: Ensure Dependencies
```bash
pip install opencv-python mediapipe pyautogui pillow pygetwindow pywin32
```

### Step 2: Run the Application
```bash
python master_gesture_controller.py
```

## 🎮 Main Gestures (Quick Reference)

### Detection Mode Entry

| Gesture | What It Does | How to Do It |
|---------|-------------|-------------|
| 👆 Thumb + Index | Enter FILE OPENING mode | Raise thumb & index finger, hold 1 sec |
| 🤚 All Fingers | Enter SCROLL mode | Open your hand flat, hold 1 sec |
| ☝️  Index Only | Enter ZOOM mode | Raise only index finger, hold 1 sec |
| ✊ Fist | Exit current mode | Close all fingers into a fist, hold 1 sec |

---

## 📁 FILE OPENING MODE Quick Gestures

| Gesture | Action |
|---------|--------|
| ✋ Pinch (thumb+index) | Select file type or open file |
| ✌️ Index+Middle Up | Go back to previous menu |
| ✊ Fist Hold | Close currently open file |
| ESC Key | Exit file mode |

---

## 📜 SCROLL MODE Quick Gestures

| Gesture | Action |
|---------|--------|
| ☝️ One finger | Scroll UP ⬆️ |
| ✌️ Two fingers | Scroll DOWN ⬇️ |
| 👍 Thumbs up only | Fast scroll UP ⬆️⬆️ |
| 🤚 Open palm | Fast scroll DOWN ⬇️⬇️ |
| ✊ Fist hold | Exit scroll mode |

---

## 🔍 ZOOM MODE Quick Gestures

| Gesture | Action |
|---------|--------|
| ☝️ Index finger | ZOOM IN 🔍+ |
| ✌️ Index+Middle | ZOOM OUT 🔍- |
| ✊ Fist hold | Exit zoom mode |

---

## 💡 Pro Tips

1. **Better Recognition**
   - Keep hand 20-80cm from camera
   - Make clear, deliberate movements
   - Hold gestures steady

2. **Faster Navigation**
   - Learn the key gestures first
   - Practice the thumb+index pinch for file selection
   - Use two-finger scroll for smooth scrolling

3. **Common Tasks**
   - **Scroll & Read**: Scroll Mode + document
   - **Zoom on PDF**: File Mode → Open PDF → Exit File Mode → Zoom Mode
   - **Quick Browse**: File Mode → Select files with pinch

---

## ⚡ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| ESC | Exit any mode / Exit application |
| - | (All actions are gesture-based) |

---

## ❓ Troubleshooting

| Problem | Solution |
|---------|----------|
| Hand not detected | Check camera is on, improve lighting |
| Gesture not working | Make gesture more deliberate, hold longer |
| Slow response | Check camera frame rate, good lighting |
| Can't exit mode | Make a clear fist and hold; if stuck, press ESC |

---

## 🎯 Example: Open PDF and Zoom

```
1. Run:  python master_gesture_controller.py
2. Display: Detection Mode
3. Gesture: Make all fingers up (palm open) → Hold 1 second
4. Display: File Opening Mode
5. Gesture: Pinch on "PDF" → Hold 0.35 seconds
6. Display: PDF files list
7. Gesture: Pinch on your PDF → Hold 0.35 seconds  
8. Result: PDF opens in Acrobat/Reader
9. Gesture: Make fist → Press ESC to exit file mode
10. Display: Detection Mode
11. Gesture: Make index finger only → Hold 1 second
12. Display: Zoom Mode
13. Gesture: Make index+middle fingers → ZOOM OUT
14. Gesture: Make fist → EXIT zoom mode
```

---

## 📊 Mode Performance

| Mode | Features | Speed |
|------|----------|-------|
| File Opening | Browse & open docs | Real-time |
| Scroll | Scroll up/down/fast | 0.8s cooldown |
| Zoom | Zoom in/out | 0.5s cooldown |

---

**That's it! You're ready to use gestures! 🎉**

For detailed information, see `MASTER_GESTURE_README.md`
