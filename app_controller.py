# app_controller.py
import os
import pygetwindow as gw
import pyautogui 
import platform
import win32api
import win32con
# ---------- File Openers ----------
def open_pdf(path):
    os.startfile(path)  


def open_pdf(path):
    os.startfile(path)
import os

def open_word(path):
    os.startfile(path)

def open_ppt(path):
    os.startfile(path)

def open_excel(path):
    os.startfile(path)


# ---------- Window Controls ----------
def close_current_window():
    window = gw.getActiveWindow()
    if window:
        window.close()

def minimize_window():
    window = gw.getActiveWindow()
    if window:
        window.minimize()

def maximize_window():
    window = gw.getActiveWindow()
    if window:
        window.maximize()


pyautogui.scroll(80)

def zoom_in():
    # Hold CTRL and scroll up (works for Word, PPT, Excel, PDF viewers)
    pyautogui.keyDown("ctrl")
    pyautogui.scroll(120)   # scroll up increases zoom
    pyautogui.keyUp("ctrl")


def zoom_out():
    # Hold CTRL and scroll down
    pyautogui.keyDown("ctrl")
    pyautogui.scroll(-120)  # scroll down decreases zoom
    pyautogui.keyUp("ctrl")