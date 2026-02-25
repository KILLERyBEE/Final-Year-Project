import cv2
import mediapipe as mp
import numpy as np
import os
import time
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


class HandFileOpener:
    def __init__(self, root_dir=None):
        self.root = Path(root_dir or Path(__file__).parent)
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.6)
        self.mp_draw = mp.solutions.drawing_utils
        self.cap = cv2.VideoCapture(0)
        self.state = 'menu'  # menu, browse, opened
        self.choice = None
        self.files = []
        self.page = 0
        self.per_page = 8
        self.last_opened = None
        self.pinched = False
        self.last_pinchtime = 0
        self.pinch_start = None
        self.PINCH_HOLD = 0.35  # seconds required to hold pinch to confirm selection
        self.cursor = None
        self.cursor_alpha = 0.35  # smoothing factor (0..1)
        self.back_start = None
        self.BACK_HOLD = 0.3
        self.FIST_HOLD = 0.35
        self.fist_start = None
        # Master-exit gesture settings (thumb + index + pinky)
        self.MASTER_EXIT_HOLD = 2.0
        self.master_exit_start = None

        self.types = [
            ('Word', ('.docx', '.doc')),
            ('PPT', ('.pptx', '.ppt')),
            ('Excel', ('.xlsx', '.xls')),
            ('PDF', ('.pdf',))
        ]

    def find_files(self, exts):
        results = []
        for dirpath, dirnames, filenames in os.walk(self.root):
            for f in filenames:
                if f.lower().endswith(exts):
                    results.append(os.path.join(dirpath, f))
        return results

    def detect_pinch(self, lm, img_w, img_h):
        # lm expected to be list of landmarks normalized
        x_thumb, y_thumb = lm[4].x * img_w, lm[4].y * img_h
        x_index, y_index = lm[8].x * img_w, lm[8].y * img_h
        dist = np.hypot(x_thumb - x_index, y_thumb - y_index)

        # compute a reference hand size (wrist to middle-finger-mcp) so thresholds scale with distance
        ref_x, ref_y = lm[9].x * img_w, lm[9].y * img_h
        wrist_x, wrist_y = lm[0].x * img_w, lm[0].y * img_h
        hand_size = np.hypot(ref_x - wrist_x, ref_y - wrist_y)
        # safety: avoid zero
        hand_size = max(hand_size, 20.0)

        # pinch triggered when thumb-index distance is small relative to hand size
        pinch_thresh = hand_size * 0.28
        is_pinched = dist < pinch_thresh
        return is_pinched, (int(x_index), int(y_index)), dist, hand_size

    def detect_fist(self, lm, img_w, img_h):
        # measure average distance of fingertips to wrist and scale by hand size
        wrist = np.array([lm[0].x * img_w, lm[0].y * img_h])
        tips_idx = [8, 12, 16, 20]
        dists = []
        for i in tips_idx:
            p = np.array([lm[i].x * img_w, lm[i].y * img_h])
            dists.append(np.linalg.norm(p - wrist))
        avg = np.mean(dists)

        # hand size reference
        ref_x, ref_y = lm[9].x * img_w, lm[9].y * img_h
        wrist_x, wrist_y = lm[0].x * img_w, lm[0].y * img_h
        hand_size = np.hypot(ref_x - wrist_x, ref_y - wrist_y)
        hand_size = max(hand_size, 20.0)

        # when fist, avg fingertip distance to wrist should be small relative to hand size
        # use a slightly more forgiving multiplier so fist works at varying distances
        return avg < (hand_size * 0.7)

    def detect_back_gesture(self, lm, img_w, img_h):
        # index and middle finger up, ring and pinky down -> back gesture
        # compare tip y to pip y: tip.y < pip.y means finger is extended (camera coords)
        try:
            idx_up = lm[8].y < lm[6].y
            mid_up = lm[12].y < lm[10].y
            ring_down = lm[16].y > lm[14].y
            pinky_down = lm[20].y > lm[18].y
            return bool(idx_up and mid_up and ring_down and pinky_down)
        except Exception:
            return False

    def close_window_by_title(self, title_substr):
        """Try several methods to close a window whose title contains title_substr.
        Returns True if a close action was performed.
        """
        title_substr = title_substr.lower()
        # try pygetwindow first
        try:
            if gw:
                wins = gw.getWindowsWithTitle(title_substr)
                # also allow partial matches
                if not wins:
                    all_w = gw.getAllTitles()
                    for t in all_w:
                        if title_substr in t.lower():
                            wins = gw.getWindowsWithTitle(t)
                            break
                for w in wins:
                    try:
                        w.activate()
                        time.sleep(0.12)
                        w.close()
                    except Exception:
                        try:
                            w.activate()
                            time.sleep(0.12)
                            pyautogui.hotkey('alt', 'f4')
                        except Exception:
                            pass
                return len(wins) > 0
        except Exception:
            pass

        # fallback to win32gui post WM_CLOSE
        try:
            if win32gui:
                closed_any = False
                def enum_cb(hwnd, extra):
                    try:
                        txt = win32gui.GetWindowText(hwnd)
                        if txt and title_substr in txt.lower():
                            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                            extra.append(hwnd)
                    except Exception:
                        pass

                matches = []
                win32gui.EnumWindows(enum_cb, matches)
                return len(matches) > 0
        except Exception:
            pass

        return False

    def run(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = self.hands.process(rgb)

            cursor = None
            pinch = False
            fist = False

            if res.multi_hand_landmarks:
                lm = res.multi_hand_landmarks[0].landmark
                pinch_res = self.detect_pinch(lm, w, h)
                if len(pinch_res) == 4:
                    pinch, cursor_pt, pinch_dist, hand_size = pinch_res
                else:
                    pinch, cursor_pt = pinch_res
                    pinch_dist, hand_size = 0, 1
                fist = self.detect_fist(lm, w, h)
                back_g = self.detect_back_gesture(lm, w, h)
                self.mp_draw.draw_landmarks(frame, res.multi_hand_landmarks[0], self.mp_hands.HAND_CONNECTIONS)

                # smooth cursor
                if cursor_pt is not None:
                    if self.cursor is None:
                        self.cursor = np.array(cursor_pt, dtype=float)
                    else:
                        self.cursor = (1 - self.cursor_alpha) * self.cursor + self.cursor_alpha * np.array(cursor_pt, dtype=float)
                    cursor = (int(self.cursor[0]), int(self.cursor[1]))

                # --- Master-exit gesture detection (thumb + index + pinky) ---
                try:
                    thumb_up = lm[4].x < lm[3].x
                    idx_up = lm[8].y < lm[6].y - 0.02
                    mid_up = lm[12].y < lm[10].y - 0.02
                    ring_up = lm[16].y < lm[14].y - 0.02
                    pinky_up = lm[20].y < lm[18].y - 0.02
                    # pattern: thumb, index, pinky up; middle and ring down
                    if thumb_up and idx_up and pinky_up and (not mid_up) and (not ring_up):
                        if self.master_exit_start is None:
                            self.master_exit_start = time.time()
                        else:
                            if time.time() - self.master_exit_start >= self.MASTER_EXIT_HOLD:
                                print("Master-exit gesture held — returning to master controller...")
                                self.cap.release()
                                cv2.destroyAllWindows()
                                return
                    else:
                        self.master_exit_start = None
                except Exception:
                    # ignore landmark indexing errors
                    self.master_exit_start = None

            # global fist-close (works from any state) - requires last_opened
            if self.last_opened and fist:
                # require hold to avoid accidental closes
                if self.fist_start is None:
                    self.fist_start = time.time()
                f_elapsed = time.time() - self.fist_start
                if cursor:
                    cv2.putText(frame, 'Close: {:.0f}%'.format(min(100, int(f_elapsed / self.FIST_HOLD * 100))), (50, 430), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 180, 180), 2)
                if f_elapsed >= self.FIST_HOLD:
                    closed = self.close_window_by_title(os.path.basename(self.last_opened))
                    if not closed:
                        try:
                            # fallback: activate and send Alt+F4
                            pyautogui.hotkey('alt', 'f4')
                            time.sleep(0.15)
                        except Exception:
                            pass
                    # clear record of last opened file
                    self.last_opened = None
                    self.fist_start = None
                    self.pinched = False
            else:
                self.fist_start = None

            # UI
            if self.state == 'menu':
                self.draw_menu(frame, cursor)
                # require pinch to be held for PINCH_HOLD seconds
                if pinch:
                    if self.pinch_start is None:
                        self.pinch_start = time.time()
                    elapsed = time.time() - self.pinch_start
                    # draw hold progress
                    if cursor:
                        cv2.circle(frame, cursor, 18, (255, 255, 255), 1)
                        if elapsed > 0:
                            pct = min(1.0, elapsed / self.PINCH_HOLD)
                            cv2.ellipse(frame, cursor, (20, 20), 0, 0, int(360 * pct), (255, 255, 255), 2)
                    if elapsed >= self.PINCH_HOLD and (not self.pinched):
                        sel = self.menu_hit_test(cursor, frame.shape)
                        if sel is not None:
                            self.choice = sel
                            self.files = self.find_files(self.types[sel][1])
                            self.page = 0
                            self.state = 'browse'
                        self.pinched = True
                        self.last_pinchtime = time.time()
                else:
                    self.pinch_start = None

            elif self.state == 'browse':
                self.draw_file_list(frame, cursor)
                # same held-pinch logic for opening files
                if pinch:
                    if self.pinch_start is None:
                        self.pinch_start = time.time()
                    elapsed = time.time() - self.pinch_start
                    if cursor:
                        cv2.circle(frame, cursor, 14, (255, 255, 255), 1)
                        if elapsed > 0:
                            pct = min(1.0, elapsed / self.PINCH_HOLD)
                            cv2.ellipse(frame, cursor, (16, 16), 0, 0, int(360 * pct), (255, 255, 255), 2)
                    if elapsed >= self.PINCH_HOLD and (not self.pinched):
                        idx = self.file_hit_test(cursor, frame.shape)
                        if idx is not None:
                            file_idx = self.page * self.per_page + idx
                            if 0 <= file_idx < len(self.files):
                                path = self.files[file_idx]
                                try:
                                    os.startfile(path)
                                    self.last_opened = path
                                    # return to main menu immediately after opening
                                    self.state = 'menu'
                                    self.choice = None
                                    self.files = []
                                    self.page = 0
                                    self.pinched = False
                                    self.pinch_start = None
                                except Exception as e:
                                    print('Open error', e)
                        self.pinched = True
                        self.last_pinchtime = time.time()
                else:
                    self.pinch_start = None

                # back gesture (index+middle) with hold to navigate back
                if back_g:
                    if self.back_start is None:
                        self.back_start = time.time()
                    back_elapsed = time.time() - self.back_start
                    if cursor:
                            cv2.putText(frame, 'Back: {:.0f}%'.format(min(100, int(back_elapsed / self.BACK_HOLD * 100))), (50, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                    if back_elapsed >= self.BACK_HOLD:
                        # go back to menu
                        self.state = 'menu'
                        self.choice = None
                        self.files = []
                        self.page = 0
                        self.back_start = None
                        self.pinched = False
                else:
                    self.back_start = None

            elif self.state == 'opened':
                self.draw_opened(frame)
                # (closing handled globally)

            # update pinch state
            if not pinch:
                self.pinched = False
                self.pinch_start = None

            cv2.imshow('File Opener', frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break

        self.cap.release()
        cv2.destroyAllWindows()

    def draw_menu(self, img, cursor):
        h, w, _ = img.shape
        start_y = 40
        gap = 80
        x = 60
        for i, (name, _) in enumerate(self.types):
            y = start_y + i * gap
            # draw thin white border box (transparent inside)
            cv2.rectangle(img, (x - 10, y - 30), (x + 220, y + 10), (255, 255, 255), 1)
            cv2.putText(img, name, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 1)
            if cursor:
                cx, cy = cursor
                if x - 10 < cx < x + 220 and y - 30 < cy < y + 10:
                    # hover: slightly thicker white border
                    cv2.rectangle(img, (x - 10, y - 30), (x + 220, y + 10), (255, 255, 255), 2)

    def menu_hit_test(self, cursor, shape):
        if not cursor:
            return None
        h, w, _ = shape
        start_y = 40
        gap = 80
        x = 60
        for i in range(len(self.types)):
            y = start_y + i * gap
            cx, cy = cursor
            if x - 10 < cx < x + 220 and y - 30 < cy < y + 10:
                return i
        return None

    def draw_file_list(self, img, cursor):
        h, w, _ = img.shape
        title = self.types[self.choice][0] + ' files'
        cv2.putText(img, title, (40, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 1)
        y0 = 80
        gap = 50
        start = self.page * self.per_page
        for i in range(self.per_page):
            idx = start + i
            y = y0 + i * gap
            if idx < len(self.files):
                name = os.path.basename(self.files[idx])
                # transparent row with thin white border
                cv2.rectangle(img, (40, y - 30), (750, y + 10), (255, 255, 255), 1)
                cv2.putText(img, name, (50, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
                if cursor:
                    cx, cy = cursor
                    if 40 < cx < 750 and y - 30 < cy < y + 10:
                        cv2.rectangle(img, (40, y - 30), (750, y + 10), (255, 255, 255), 2)

    def file_hit_test(self, cursor, shape):
        if not cursor:
            return None
        h, w, _ = shape
        y0 = 80
        gap = 50
        for i in range(self.per_page):
            y = y0 + i * gap
            cx, cy = cursor
            if 40 < cx < 750 and y - 30 < cy < y + 10:
                return i
        return None

    def draw_opened(self, img):
        h, w, _ = img.shape
        txt = 'Opened: ' + (os.path.basename(self.last_opened) if self.last_opened else '')
        # transparent header with thin white border
        cv2.rectangle(img, (20, 20), (w - 20, 70), (255, 255, 255), 1)
        cv2.putText(img, txt, (40, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 1)


def main():
    opener = HandFileOpener()
    print('Starting hand-driven file opener. ESC to quit.')
    opener.run()


if __name__ == '__main__':
    main()
