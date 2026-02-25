"""video_control.py
Refactored gesture-driven video browser and media controls.

Features:
- Lists videos from VIDEO_FOLDER
- Pinch+hold to open selected video (prefers VLC if installed)
- Fist+hold closes the last opened player (uses process PID when available)
- Open-palm: Play/Pause, Index-only: Next, Index+middle: Previous (hold to confirm)

Notes:
- Optional dependencies: `psutil` (better process detection), `pygetwindow`/`pywin32` (window close helpers)
- This file is intentionally simpler and more robust than the previous iterative edits.
"""
import os
import time
import subprocess
from pathlib import Path
try:
    import winsound
except Exception:
    winsound = None

import cv2
import mediapipe as mp
import numpy as np

try:
    import psutil
except Exception:
    psutil = None

try:
    import pygetwindow as gw
except Exception:
    gw = None

import ctypes
user32 = ctypes.windll.user32

# Media key constants
KEYEVENTF_KEYUP = 0x0002
VK_MEDIA_NEXT = 0xB0
VK_MEDIA_PREV = 0xB1
VK_MEDIA_PLAY_PAUSE = 0xB3

def send_media_key(vk):
    try:
        user32.keybd_event(vk, 0, 0, 0)
        time.sleep(0.05)
        user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
    except Exception:
        pass


VIDEO_DIR = Path(__file__).parent / 'VIDEO_FOLDER'
VIDEO_EXTS = ('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.webm')

def find_videos():
    vids = []
    if not VIDEO_DIR.exists():
        return vids
    for root, _, files in os.walk(VIDEO_DIR):
        for f in files:
            if f.lower().endswith(VIDEO_EXTS):
                vids.append(os.path.join(root, f))
    vids.sort()
    return vids


def find_vlc_exe():
    # prefer vlc so we can track the PID
    vlc = shutil_which('vlc')
    if vlc:
        return vlc
    # common install paths
    candidates = [
        os.path.join(os.environ.get('ProgramFiles', ''), 'VideoLAN', 'VLC', 'vlc.exe'),
        os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'VideoLAN', 'VLC', 'vlc.exe'),
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None


def shutil_which(name):
    try:
        from shutil import which
        return which(name)
    except Exception:
        return None


def detect_spawned_pids(target_path, sleep=0.6):
    """Attempt to detect newly spawned processes that reference target_path (requires psutil)."""
    if not psutil:
        return []
    before = {p.pid for p in psutil.process_iter(attrs=['pid'])}
    time.sleep(sleep)
    found = []
    target_basename = os.path.basename(target_path).lower()
    for p in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
        try:
            if p.pid in before:
                continue
            name = (p.info.get('name') or '').lower()
            cmd = ' '.join(p.info.get('cmdline') or []).lower()
            if target_basename in cmd or target_basename in name or any(k in name for k in ('vlc','mpv','wmplayer','potplayer','mpc')):
                found.append(p.pid)
        except Exception:
            continue
    return found


class VideoController:
    def __init__(self):
        self.videos = find_videos()
        self.last_pid = None
        self.last_path = None

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.6)
        self.mp_draw = mp.solutions.drawing_utils

        self.cap = cv2.VideoCapture(0)
        self.cursor = None
        self.cursor_smooth = None
        self.CURSOR_ALPHA = 0.35

        self.COOLDOWN = 0.9
        self.last_action = 0
        self.HOLD_TIME = 0.45

        self.play_start = None
        self.next_start = None
        self.prev_start = None
        self.exit_start = None
        self.pinch_start = None

    def hand_size(self, lm, w, h):
        ref_x, ref_y = lm[9].x * w, lm[9].y * h
        wrist_x, wrist_y = lm[0].x * w, lm[0].y * h
        return max(20.0, np.hypot(ref_x - wrist_x, ref_y - wrist_y))

    def is_fist(self, lm, w, h):
        wrist = np.array([lm[0].x * w, lm[0].y * h])
        tips = [8, 12, 16, 20]
        dists = [np.linalg.norm(np.array([lm[i].x * w, lm[i].y * h]) - wrist) for i in tips]
        avg = np.mean(dists)
        hs = self.hand_size(lm, w, h)
        return avg < (hs * 0.75)

    def finger_up(self, lm, tip, pip):
        return lm[tip].y < lm[pip].y

    def detect_pinch(self, lm, w, h):
        x_thumb, y_thumb = lm[4].x * w, lm[4].y * h
        x_index, y_index = lm[8].x * w, lm[8].y * h
        dist = np.hypot(x_thumb - x_index, y_thumb - y_index)
        hs = self.hand_size(lm, w, h)
        thresh = hs * 0.28
        return dist < thresh, (int(x_index), int(y_index))

    def can_trigger(self):
        if time.time() - self.last_action > self.COOLDOWN:
            self.last_action = time.time()
            return True
        return False

    def open_video(self, path):
        # prefer VLC so we can control/close reliably
        vlc = find_vlc_exe()
        if vlc:
            try:
                proc = subprocess.Popen([vlc, '--play-and-exit', path])
                self.last_pid = proc.pid
                self.last_path = path
                return True
            except Exception:
                pass

        # fallback: start default handler and try to detect spawned pid (requires psutil)
        try:
            os.startfile(path)
            pids = detect_spawned_pids(path)
            if pids:
                self.last_pid = pids[0]
                self.last_path = path
            else:
                self.last_pid = None
                self.last_path = path
            return True
        except Exception:
            return False

    def close_last(self):
        if not self.last_path and not self.last_pid:
            try:
                if winsound:
                    winsound.Beep(600, 120)
            except Exception:
                pass
            return False

        closed = False
        # try to close by PID (psutil)
        if self.last_pid and psutil:
            try:
                p = psutil.Process(self.last_pid)
                p.terminate()
                try:
                    p.wait(timeout=1.0)
                except Exception:
                    p.kill()
                closed = True
            except Exception:
                closed = False

        # try title/window close via pygetwindow as fallback
        if not closed and gw and self.last_path:
            try:
                title_sub = os.path.basename(self.last_path)
                wins = gw.getWindowsWithTitle(title_sub)
                for w in wins:
                    try:
                        w.close()
                        closed = True
                    except Exception:
                        pass
            except Exception:
                pass

        if closed:
            try:
                if winsound:
                    winsound.Beep(800, 120)
            except Exception:
                pass
            self.last_pid = None
            self.last_path = None
            return True

        return False

    def run(self):
        cv2.namedWindow('Video Control', cv2.WINDOW_NORMAL)
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = self.hands.process(rgb)

            gesture = None
            cursor = None

            if result.multi_hand_landmarks:
                lm = result.multi_hand_landmarks[0].landmark
                self.mp_draw.draw_landmarks(frame, result.multi_hand_landmarks[0], self.mp_hands.HAND_CONNECTIONS)

                # cursor smoothing
                raw = (int(lm[8].x * w), int(lm[8].y * h))
                if self.cursor_smooth is None:
                    self.cursor_smooth = np.array(raw, dtype=float)
                else:
                    self.cursor_smooth = (1 - self.CURSOR_ALPHA) * self.cursor_smooth + self.CURSOR_ALPHA * np.array(raw, dtype=float)
                cursor = (int(self.cursor_smooth[0]), int(self.cursor_smooth[1]))

                index_up = self.finger_up(lm, 8, 6)
                middle_up = self.finger_up(lm, 12, 10)
                ring_up = self.finger_up(lm, 16, 14)
                fist = self.is_fist(lm, w, h)
                pinch, pinch_pt = self.detect_pinch(lm, w, h)

                # Fist -> close
                if fist:
                    gesture = 'exit'
                    if self.exit_start is None:
                        self.exit_start = time.time()
                    if time.time() - self.exit_start >= self.HOLD_TIME and self.can_trigger():
                        self.close_last()
                        self.exit_start = None
                else:
                    self.exit_start = None

                # Index-only -> Next
                if index_up and not middle_up and not ring_up:
                    gesture = 'next'
                    if self.next_start is None:
                        self.next_start = time.time()
                    if time.time() - self.next_start >= self.HOLD_TIME and self.can_trigger():
                        send_media_key(VK_MEDIA_NEXT)
                        try:
                            if winsound:
                                winsound.Beep(1200, 100)
                        except Exception:
                            pass
                        self.next_start = None
                else:
                    self.next_start = None

                # Index+middle -> Prev
                if index_up and middle_up and not ring_up:
                    gesture = 'prev'
                    if self.prev_start is None:
                        self.prev_start = time.time()
                    if time.time() - self.prev_start >= self.HOLD_TIME and self.can_trigger():
                        send_media_key(VK_MEDIA_PREV)
                        try:
                            if winsound:
                                winsound.Beep(900, 100)
                        except Exception:
                            pass
                        self.prev_start = None
                else:
                    self.prev_start = None

                # Open palm -> Play/Pause
                if index_up and middle_up and ring_up:
                    gesture = 'play'
                    if self.play_start is None:
                        self.play_start = time.time()
                    if time.time() - self.play_start >= self.HOLD_TIME and self.can_trigger():
                        send_media_key(VK_MEDIA_PLAY_PAUSE)
                        try:
                            if winsound:
                                winsound.Beep(1000, 100)
                        except Exception:
                            pass
                        self.play_start = None
                else:
                    self.play_start = None

            # UI: header + debug
            cv2.putText(frame, 'Video Control — hold gesture to confirm', (12, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1)
            if gesture:
                cv2.putText(frame, f'Detected: {gesture}', (12, h-20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
            if cursor:
                cv2.circle(frame, cursor, 6, (255,255,255), -1)

            # draw video list
            col_x1 = w - 360
            col_x2 = w - 12
            cv2.rectangle(frame, (col_x1, 56), (col_x2, h-16), (240,240,240), -1)
            cv2.rectangle(frame, (col_x1, 56), (col_x2, h-16), (180,180,180), 1)
            cv2.putText(frame, 'Videos:', (col_x1+10, 76), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (20,20,20), 1)

            gap = 38
            for i, p in enumerate(self.videos[:10]):
                y = 86 + i*gap
                name = os.path.basename(p)
                short = name if len(name) < 36 else name[:33] + '...'
                cv2.putText(frame, short, (col_x1+12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (10,10,10), 1)
                # hover/open
                if cursor and (col_x1 < cursor[0] < col_x2) and (y-20 < cursor[1] < y+6):
                    cv2.rectangle(frame, (col_x1+2, y-22), (col_x2-2, y+8), (150,150,150), 2)
                    if pinch:
                        if self.pinch_start is None:
                            self.pinch_start = time.time()
                        if time.time() - self.pinch_start >= self.HOLD_TIME:
                            opened = self.open_video(p)
                            if opened:
                                try:
                                    if winsound:
                                        winsound.Beep(1200, 120)
                                except Exception:
                                    pass
                            self.pinch_start = None
                    else:
                        self.pinch_start = None

            cv2.imshow('Video Control', frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break

        self.cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    vc = VideoController()
    vc.run()
