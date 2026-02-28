"""video_player.py
Gesture-driven video browser for the Final Year Project master controller.

Features
--------
- Scans VIDEO_FOLDER for common video file types.
- Displays them in a paginated list in an OpenCV window (same style as open_files.py).
- Pinch gesture (thumb + index, held for PINCH_HOLD seconds) → opens selected video
  in the system default external player via os.startfile().
- All-five-fingers-up gesture held for PALM_HOLD seconds → toggles Play/Pause via
  the Windows media-key API (works with most media players).
  A 2-second cooldown prevents accidental double-triggers.
- Back gesture (index + middle up, others down) held for BACK_HOLD seconds → previous page.
- Master-exit gesture (thumb + index + pinky, others down) held for MASTER_EXIT_HOLD
  seconds → releases camera and returns to master controller.
- ESC key → quit.

Gesture summary
---------------
  Pinch          (thumb ∩ index touching)          → open highlighted video
  Open palm      (all 5 fingers up, held 2 s)      → play / pause toggle
  Peace sign     (index + middle up)               → go back to previous page / menu
  Thumb+Idx+Pinky (held 2 s)                       → exit back to master controller
  ESC key                                          → quit immediately
"""

import cv2
import mediapipe as mp
import numpy as np
import os
import time
import ctypes
import pyautogui
from pathlib import Path

try:
    import pygetwindow as gw
except Exception:
    gw = None

try:
    import win32gui
    import win32con
except Exception:
    win32gui = None
    win32con = None

# ---------------------------------------------------------------------------
# Optional Windows media-key support
# ---------------------------------------------------------------------------
try:
    _user32 = ctypes.windll.user32
    _KEYEVENTF_KEYUP  = 0x0002
    _VK_MEDIA_PLAY_PAUSE = 0xB3

    def _send_play_pause():
        _user32.keybd_event(_VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
        time.sleep(0.05)
        _user32.keybd_event(_VK_MEDIA_PLAY_PAUSE, 0, _KEYEVENTF_KEYUP, 0)

except Exception:
    def _send_play_pause():
        pass  # non-Windows fallback

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
VIDEO_FOLDER = Path(__file__).parent / 'VIDEO_FOLDER'
VIDEO_EXTS   = ('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.webm', '.flv', '.m4v')

PINCH_HOLD        = 0.4   # seconds to hold pinch to confirm file open
BACK_HOLD         = 0.35  # seconds to hold back gesture to confirm
FIST_HOLD         = 0.5   # seconds to hold fist to close video
PALM_HOLD         = 1.0   # seconds to hold open palm for play/pause
PALM_COOLDOWN     = 1.5   # cooldown between consecutive play/pause triggers
MASTER_EXIT_HOLD  = 2.0   # seconds to hold master-exit gesture
CURSOR_ALPHA      = 0.35  # lower = smoother cursor (exponential moving average)
PER_PAGE          = 8     # files per page in the browser

# Colours (BGR)
C_WHITE   = (255, 255, 255)
C_BLACK   = (0,   0,   0  )
C_GREEN   = (80,  220, 100)
C_CYAN    = (220, 220, 80 )
C_RED_ISH = (100, 130, 255)
C_PALM    = (80,  255, 180)
C_HEADER  = (30,  30,  60 )
C_ROW_HL  = (60,  60,  100)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_videos():
    """Return sorted list of absolute paths to video files in VIDEO_FOLDER."""
    results = []
    if not VIDEO_FOLDER.exists():
        return results
    for dirpath, _, filenames in os.walk(VIDEO_FOLDER):
        for f in filenames:
            if f.lower().endswith(VIDEO_EXTS):
                results.append(os.path.join(dirpath, f))
    return sorted(results)


def _hand_size(lm, w, h):
    """Wrist-to-MCP reference distance, clamped to ≥ 20 px."""
    ref   = np.array([lm[9].x * w,  lm[9].y  * h])
    wrist = np.array([lm[0].x * w,  lm[0].y  * h])
    return max(20.0, float(np.linalg.norm(ref - wrist)))


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class VideoPlayer:
    """Gesture-driven video browser with external-player launch."""

    def __init__(self):
        self.videos = find_videos()
        self.page   = 0

        # MediaPipe
        self.mp_hands = mp.solutions.hands
        self.hands    = self.mp_hands.Hands(max_num_hands=1,
                                            min_detection_confidence=0.65,
                                            min_tracking_confidence=0.65)
        self.mp_draw  = mp.solutions.drawing_utils

        # Camera
        self.cap = cv2.VideoCapture(0)


        # Gesture timers  (None = not currently timing)
        self.pinch_start:        float | None = None
        self.back_start:         float | None = None
        self.master_exit_start:  float | None = None
        self.palm_start:         float | None = None
        self.fist_start:         float | None = None
        self.last_palm_action:   float        = 0.0
        self.pinched:            bool         = False
        self._palm_holding:      bool         = False
        self._fist_holding:      bool         = False

        # Playback state tracking (for on-screen display only)
        self.is_paused:   bool         = False
        self.last_opened: str | None   = None   # basename of last opened file

        # Cursor smoothing  (np.ndarray | None)
        self.cursor_smooth = None

    # ------------------------------------------------------------------
    # Gesture detectors
    # ------------------------------------------------------------------

    def _detect_pinch(self, lm, w, h):
        """Returns (is_pinched, cursor_point)."""
        tx, ty = lm[4].x * w, lm[4].y * h
        ix, iy = lm[8].x * w, lm[8].y * h
        dist   = np.hypot(tx - ix, ty - iy)
        hs     = _hand_size(lm, w, h)
        return dist < hs * 0.28, (int(ix), int(iy))

    def _detect_fist(self, lm, w, h):
        wrist = np.array([lm[0].x * w, lm[0].y * h])
        tips  = [8, 12, 16, 20]
        avg   = np.mean([np.linalg.norm(np.array([lm[i].x * w, lm[i].y * h]) - wrist)
                         for i in tips])
        return avg < _hand_size(lm, w, h) * 0.72

    def _detect_back_gesture(self, lm):
        """index + middle up, ring + pinky down."""
        try:
            return (lm[8].y  < lm[6].y  and
                    lm[12].y < lm[10].y and
                    lm[16].y > lm[14].y and
                    lm[20].y > lm[18].y)
        except Exception:
            return False

    def _detect_open_palm(self, lm):
        """All four fingers AND thumb clearly extended."""
        try:
            thumb_ext  = abs(lm[4].x - lm[2].x) > 0.04
            index_ext  = lm[8].y  < lm[6].y  - 0.02
            middle_ext = lm[12].y < lm[10].y - 0.02
            ring_ext   = lm[16].y < lm[14].y - 0.02
            pinky_ext  = lm[20].y < lm[18].y - 0.02
            return thumb_ext and index_ext and middle_ext and ring_ext and pinky_ext
        except Exception:
            return False

    def _detect_master_exit(self, lm):
        """Thumb + index + pinky up; middle + ring down."""
        try:
            thumb_up  = lm[4].x < lm[3].x
            idx_up    = lm[8].y  < lm[6].y  - 0.02
            mid_up    = lm[12].y < lm[10].y - 0.02
            ring_up   = lm[16].y < lm[14].y - 0.02
            pinky_up  = lm[20].y < lm[18].y - 0.02
            return thumb_up and idx_up and pinky_up and (not mid_up) and (not ring_up)
        except Exception:
            return False

    def _close_video(self):
        """Attempt to close the externally opened video player window."""
        if not self.last_opened:
            return False
        title_sub = self.last_opened.lower()
        closed = False

        # Method 1: pygetwindow
        try:
            if gw:
                wins = gw.getAllWindows()
                matches = [w for w in wins if title_sub in w.title.lower()]
                for w in matches:
                    try:
                        w.activate()
                        time.sleep(0.1)
                        w.close()
                        closed = True
                    except Exception:
                        pass
        except Exception:
            pass

        # Method 2: win32gui WM_CLOSE
        if not closed:
            try:
                if win32gui and win32con:
                    found = []
                    def _cb(hwnd, extra):
                        txt = win32gui.GetWindowText(hwnd)
                        if txt and title_sub in txt.lower():
                            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                            extra.append(hwnd)
                    win32gui.EnumWindows(_cb, found)
                    if found:
                        closed = True
            except Exception:
                pass

        # Method 3: Alt+F4 fallback
        if not closed:
            try:
                pyautogui.hotkey('alt', 'f4')
                closed = True
            except Exception:
                pass

        if closed:
            print(f'[VideoPlayer] Closed: {self.last_opened}')
            self.last_opened = None
            self.is_paused   = False
        return closed

    # ------------------------------------------------------------------
    # Hit-test (which row is the cursor hovering over?)
    # ------------------------------------------------------------------

    def _row_hit(self, cursor, y0, gap, n):
        if not cursor:
            return None
        cx, cy = cursor
        for i in range(n):
            y = y0 + i * gap
            if 40 < cx < 760 and y - 28 < cy < y + 10:
                return i
        return None

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _draw_browser(self, frame, cursor, pinch, pinch_elapsed):
        h, w, _ = frame.shape

        # Dark header
        cv2.rectangle(frame, (0, 0), (w, 55), C_HEADER, -1)
        cv2.putText(frame, 'VIDEO PLAYER', (16, 36),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, C_WHITE, 2)
        page_total = max(1, (len(self.videos) + PER_PAGE - 1) // PER_PAGE)
        cv2.putText(frame, f'Page {self.page + 1}/{page_total}', (w - 160, 36),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, C_CYAN, 1)

        # File list
        y0  = 90
        gap = 55
        start = self.page * PER_PAGE
        hovered_row = self._row_hit(cursor, y0, gap, PER_PAGE)

        for i in range(PER_PAGE):
            idx = start + i
            y   = y0 + i * gap
            if idx >= len(self.videos):
                break

            name  = os.path.basename(self.videos[idx])
            short = name if len(name) < 52 else name[:49] + '...'

            is_hover = (hovered_row == i)
            box_col  = C_ROW_HL if is_hover else (20, 20, 40)
            txt_col  = C_GREEN  if is_hover else C_WHITE
            border_t = 2        if is_hover else 1

            cv2.rectangle(frame, (38, y - 28), (762, y + 12), box_col,  -1)
            cv2.rectangle(frame, (38, y - 28), (762, y + 12), C_WHITE, border_t)
            cv2.putText(frame, short, (52, y), cv2.FONT_HERSHEY_SIMPLEX, 0.62, txt_col, 1)

            # pinch progress arc on hovered row
            if is_hover and pinch and pinch_elapsed > 0 and cursor:
                pct = min(1.0, pinch_elapsed / PINCH_HOLD)
                cv2.ellipse(frame, cursor, (22, 22), 0, 0, int(360 * pct), C_GREEN, 2)

        # Bottom hints
        hint_y = h - 10
        cv2.putText(frame, 'PINCH=Open | FIST=Close | PEACE=Prev Page | ALL FINGERS (2s)=Play/Pause | T+I+Pinky(2s)=Exit',
                    (12, hint_y), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (180, 180, 180), 1)

        # Cursor dot
        if cursor:
            cv2.circle(frame, cursor, 8, C_WHITE, -1)

        # Fist hold progress bar (red)
        if self._fist_holding:
            elapsed = time.time() - self.fist_start if self.fist_start else 0
            pct     = min(1.0, elapsed / FIST_HOLD)
            bar_w   = int(pct * (w - 40))
            cv2.rectangle(frame, (20, h - 58), (20 + bar_w, h - 44), (60, 60, 220), -1)
            cv2.rectangle(frame, (20, h - 58), (w - 20,     h - 44), C_WHITE, 1)
            cv2.putText(frame, f'CLOSING...  {int(pct*100)}%', (24, h - 46),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (120, 120, 255), 1)

        # Palm hold progress bar (green)
        if self._palm_holding:
            elapsed   = time.time() - self.palm_start if self.palm_start else 0
            pct       = min(1.0, elapsed / PALM_HOLD)
            bar_w     = int(pct * (w - 40))
            lbl       = 'PAUSING...' if not self.is_paused else 'RESUMING...'
            cv2.rectangle(frame, (20, h - 38), (20 + bar_w, h - 22), C_PALM, -1)
            cv2.rectangle(frame, (20, h - 38), (w - 20,     h - 22), C_WHITE,  1)
            cv2.putText(frame, f'{lbl}  {int(pct*100)}%', (24, h - 24),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, C_PALM, 1)

        # Status: show last opened + play state
        if self.last_opened:
            state_lbl = '⏸ PAUSED' if self.is_paused else '▶ PLAYING'
            cv2.putText(frame, f'{state_lbl}: {self.last_opened}', (12, h - 48),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, C_CYAN, 1)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        self._palm_holding = False  # reset on each run() call

        print('\n========== VIDEO PLAYER MODE ==========')
        print('  PINCH on a file         → open in default player')
        print('  All fingers up (2 sec)  → play / pause toggle')
        print('  Peace sign (back)       → previous page')
        print('  Thumb+Index+Pinky (2s)  → exit to master controller')
        print('  ESC                     → quit')
        print('========================================\n')

        if not self.videos:
            print(f'[VideoPlayer] No videos found in {VIDEO_FOLDER}')

        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = self.hands.process(rgb)

            cursor       = None
            pinch        = False
            pinch_pt     = None
            pinch_elapsed = 0.0
            back_g       = False
            open_palm    = False

            if res.multi_hand_landmarks:
                lm = res.multi_hand_landmarks[0].landmark
                self.mp_draw.draw_landmarks(frame,
                                            res.multi_hand_landmarks[0],
                                            self.mp_hands.HAND_CONNECTIONS)

                # Smooth cursor (index fingertip)
                raw_pt = np.array([lm[8].x * w, lm[8].y * h])
                if self.cursor_smooth is None:
                    self.cursor_smooth = raw_pt.copy()
                else:
                    self.cursor_smooth = ((1 - CURSOR_ALPHA) * self.cursor_smooth
                                          + CURSOR_ALPHA * raw_pt)
                cursor = (int(self.cursor_smooth[0]), int(self.cursor_smooth[1]))

                pinch, pinch_pt = self._detect_pinch(lm, w, h)
                back_g          = self._detect_back_gesture(lm)
                open_palm       = self._detect_open_palm(lm)

                # ── Fist → close video ──────────────────────────────
                fist = self._detect_fist(lm, w, h)
                self._fist_holding = fist and (self.last_opened is not None)
                if fist and self.last_opened:
                    if self.fist_start is None:
                        self.fist_start = time.time()
                    fist_elapsed = time.time() - self.fist_start
                    if fist_elapsed >= FIST_HOLD:
                        self._close_video()
                        self.fist_start = None
                else:
                    self.fist_start = None

                # ── Master-exit gesture ──────────────────────────────
                if self._detect_master_exit(lm):
                    if self.master_exit_start is None:
                        self.master_exit_start = time.time()
                    elif time.time() - self.master_exit_start >= MASTER_EXIT_HOLD:
                        print('[VideoPlayer] Master-exit gesture → returning to controller')
                        self._cleanup()
                        return
                else:
                    self.master_exit_start = None

                # ── Open-palm → play / pause (hold PALM_HOLD secs) ──
                self._palm_holding = open_palm
                if open_palm:
                    if self.palm_start is None:
                        self.palm_start = time.time()
                    palm_elapsed = time.time() - self.palm_start
                    if (palm_elapsed >= PALM_HOLD and
                            time.time() - self.last_palm_action >= PALM_COOLDOWN):
                        _send_play_pause()
                        self.is_paused      = not self.is_paused
                        self.last_palm_action = time.time()
                        self.palm_start       = None
                        print('[VideoPlayer] Play/Pause toggled →',
                              'PAUSED' if self.is_paused else 'PLAYING')
                else:
                    self.palm_start = None

                # ── Back gesture → previous page ────────────────────
                if back_g and not pinch:
                    if self.back_start is None:
                        self.back_start = time.time()
                    back_elapsed = time.time() - self.back_start
                    if back_elapsed >= BACK_HOLD:
                        if self.page > 0:
                            self.page -= 1
                        self.back_start = None
                        self.pinched    = False
                else:
                    self.back_start = None

                # ── Pinch → open video ───────────────────────────────
                hovered_row = self._row_hit(cursor, 90, 55, PER_PAGE)
                if pinch and hovered_row is not None:
                    if self.pinch_start is None:
                        self.pinch_start = time.time()
                    pinch_elapsed = time.time() - self.pinch_start

                    if pinch_elapsed >= PINCH_HOLD and not self.pinched:
                        file_idx = self.page * PER_PAGE + hovered_row
                        if 0 <= file_idx < len(self.videos):
                            path = self.videos[file_idx]
                            try:
                                os.startfile(path)
                                self.last_opened = os.path.basename(path)
                                self.is_paused   = False
                                print(f'[VideoPlayer] Opened: {path}')
                            except Exception as e:
                                print(f'[VideoPlayer] Open error: {e}')
                        # Next page if no more rows visible
                        elif file_idx >= len(self.videos):
                            page_total = max(1, (len(self.videos) + PER_PAGE - 1) // PER_PAGE)
                            if self.page + 1 < page_total:
                                self.page += 1
                        self.pinched    = True
                        self.pinch_start = None
                elif not pinch:
                    self.pinch_start = None

                # Reset pinch guard once finger released
                if not pinch:
                    self.pinched = False

            else:
                # No hand detected — reset all timers
                self.cursor_smooth     = None
                self.pinch_start       = None
                self.pinched           = False
                self.back_start        = None
                self.palm_start        = None
                self.fist_start        = None
                self.master_exit_start = None
                self._palm_holding     = False
                self._fist_holding     = False

            # ── Draw UI ─────────────────────────────────────────────
            self._draw_browser(frame, cursor, pinch, pinch_elapsed)

            cv2.imshow('Video Player', frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 27:   # ESC
                break

        self._cleanup()

    def _cleanup(self):
        self.cap.release()
        cv2.destroyAllWindows()


# ---------------------------------------------------------------------------
# Entry point (standalone run)
# ---------------------------------------------------------------------------

def run_video_player():
    """Called by master_gesture_controller to launch this mode."""
    vp = VideoPlayer()
    vp.run()


if __name__ == '__main__':
    run_video_player()
