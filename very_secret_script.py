# -*- coding: utf-8 -*-

import json
import sys
import threading
import time
import win32api
import win32con
import winsound
import win32gui
from image_search import get_screen_area_as_image, load_image_from_file, search_image_in_image, AimBot
from overlay_label import OverlayLabel
from keyboard_input import keyb_down, keyb_up

from ctypes import windll, Structure, c_long, byref


class POINT(Structure):
    _fields_ = [("x", c_long), ("y", c_long)]

def cursor():
    hcursor = win32gui.GetCursorInfo()[1]
    return hcursor==0

LMB = win32con.VK_LBUTTON
F4 = win32con.VK_F4
F10 = win32con.VK_F10
NUM_4 = win32con.VK_F5
NUM_6 = win32con.VK_F6
KEY_1 = 0x31
KEY_2 = 0x32
KEY_3 = 0x33
KEY_E = 0x45
KEY_R = 0x52

EMPTY_WEAPONS_LIST = [
    {
        "name": "None",
        "rpm": 6000,
        "check_image": None,
        "check_area": [1500, 950, 1735, 1030],
        "pattern": [
            [0,0],
        ]
    },
]

def queryMousePosition():
    pt = POINT()
    windll.user32.GetCursorPos(byref(pt))
    return pt.x, pt.y

def beep_on():
    winsound.Beep(2000, 100)


def beep_off():
    winsound.Beep(1000, 100)


def beep_exit():
    winsound.Beep(500, 500)


def mouse_move_relative(dx, dy):
    win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(dx), int(dy), 0, 0)


def lmb_down():
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)


def lmb_up():
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)


def rmb_down():
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0)


def rmb_up():
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0)


def is_lmb_pressed():
    return win32api.GetKeyState(LMB) < 0


def load_weapons(weapon_filename):
    weapons_list = EMPTY_WEAPONS_LIST
    current_weapon_index = 0

    if not weapon_filename:
        print("WARNING: Filename with weapons data was not set! Meh!?")
        return weapons_list, current_weapon_index

    weapon_filepath = "./weapon_data/{}.json".format(weapon_filename)

    print("DEBUG: Trying to open and load data from {}".format(weapon_filepath))
    try:
        with open(weapon_filepath) as f:
            data = json.load(f)
            weapons_data = data["weapons"]
    except:
        print("ERROR: Can not open/read file with weapon data. No file? Corrupted? WTF!?")
        print("INFO: Since last error I will use default EMPTY_WEAPONS_LIST. Go check your data files, okay?")
        return weapons_list, current_weapon_index
    print("DEBUG: Not sure but looks like everything is okay :)")

    weapons_list = weapons_data

    for i, weapon in enumerate(weapons_list):
        if weapon["check_image"]:
            image = load_image_from_file("./weapon_data/{}_img\{}".format(weapon_filename, weapon["check_image"]))
            weapons_list[i]["image"] = image
        else:
            weapons_list[i]["image"] = None

    return weapons_list, current_weapon_index


def toggle_recoil(no_recoil):
    if no_recoil:
        beep_off()
        print('OFF')
    else:
        beep_on()
        print('ON')
    return not no_recoil


def prev_weapon(weapons_list, current_weapon_index):
    if current_weapon_index < 1:
        current_weapon_index = len(weapons_list) - 1
    else:
        current_weapon_index -= 1
    return current_weapon_index


def next_weapon(weapons_list, current_weapon_index):
    if current_weapon_index > len(weapons_list) - 2:
        current_weapon_index = 0
    else:
        current_weapon_index += 1
    return current_weapon_index


def get_tick(rpm):
    rps = rpm/60
    mstick = 1000.0/rps
    stick = round(mstick/1000, 3)
    return stick


def construct_overlay(overlay, weapons_list, current_weapon_index, no_recoil):
    recoil_data = "ON" if no_recoil else "OFF"
    bg_data = "#acffac" if no_recoil else "#ffacac"
    recoil_string = "NoRecoil: {}".format(recoil_data)
    weapon_string = "Weapon: {}".format(weapons_list[current_weapon_index]["name"])
    length = max(len(recoil_string), len(weapon_string))
    overlay_string = "{}\n{}".format(recoil_string.ljust(length), weapon_string.ljust(length))
    overlay.set_bg(bg_data)
    overlay.set_text(overlay_string)

def process_no_recoil( weapons_list, current_weapon_index, no_recoil):
    shot_index = 0
    # prev_secs = 0
    prev_x = 0
    prev_y = 0
    # time_points = weapons_list[current_weapon_index]["time_points"]
    shot_tick = get_tick(weapons_list[current_weapon_index]["rpm"])
    mx = weapons_list[current_weapon_index]["x"]
    my = weapons_list[current_weapon_index]["y"]
    # if time_points > mx:
    #     time_points = time_points[:len(mx)]

    t = 0
    # timer_govna = time.time()*1000
    while is_lmb_pressed():
        if t < time.perf_counter():
            if shot_index < len(mx) - 1:
                dx = -(mx[shot_index] - prev_x)/1.5
                dy = -(my[shot_index] - prev_y)/1.5
                prev_x = mx[shot_index]
                prev_y = my[shot_index]
                mouse_move_relative(dx, dy)
                #time.sleep((time_points[shot_index]-prev_secs)/1300)
                # t = time.perf_counter() + (time_points[shot_index]-prev_secs)/1000  - 0.01
                t = time.perf_counter() + (shot_tick) - 0.01
                # prev_secs = time_points[shot_index]
                shot_index += 1
                # print(time.time()*1000 - timer_govna)
                timer_govna = time.time()*1000


def shot_thread(dx, dy, delay,start):
    time.sleep(delay)
    print(1000*(time.time()-start))
    mouse_move_relative(dx, dy)


def fit_resolution(area):
    result = []
    # print(area)
    for point in area:
        result.append(point * 1.33333333333333)
    return result

def detect_current_weapon(weapons_list):
    image_to_check = get_screen_area_as_image([1570, 960, 1700, 1000])
    for index, weapon in enumerate(weapons_list):
        if weapon["image"] is not None:
            # image_to_check = get_screen_area_as_image(weapon["check_area"])
            # print(weapon["name"])
            found_xy = search_image_in_image(weapon["image"], image_to_check)
            if found_xy:
                return index
    return None

class WeaponDetectorThread(threading.Thread):
    def __init__(self, weapon_list):
        threading.Thread.__init__(self)
        self.weapon_list = weapon_list
        self.out = None
        self.no_recoil = False
        self.shutdown = False

    def run(self):
        while not self.shutdown:
            if self.no_recoil:
                weapon_autodetect = detect_current_weapon(self.weapon_list)
                self.out = weapon_autodetect
            time.sleep(0.05)

    def terminate(self):
        self.shutdown = True


def main(weapon_filename):
    # time.sleep(2)
    # aim = AimBot()

    running = True
    no_recoil = False
    no_aim = False
    weapons_list, current_weapon_index = load_weapons(weapon_filename)
    # overlay = OverlayLabel()
    # overlay.set_size(20, 2)  # size in symbols
    print("INFO: Starting WeaponDetector daemon...")
    weapon_detector = WeaponDetectorThread(weapons_list)
    weapon_detector.setDaemon(True)
    weapon_detector.start()
    print("INFO: Everything looks ok, so I'm going to my general routine ;)")

    prev_x, prev_y = queryMousePosition()
    while running:
        if weapon_detector.out is not None:
           current_weapon_index = weapon_detector.out
           print(weapons_list[current_weapon_index]["name"], end='\r')
        # construct_overlay(overlay, weapons_list, current_weapon_index, no_recoil)
        if win32api.GetAsyncKeyState(F4):
            no_recoil = toggle_recoil(no_recoil)
            # no_aim= toggle_recoil(no_aim)
            weapon_detector.no_recoil = no_recoil
            time.sleep(0.2)
        if win32api.GetAsyncKeyState(F10):
            running = not running
            beep_exit()
            weapon_detector.terminate()
            print("INFO: Exiting!")
            time.sleep(0.5)
        if win32api.GetAsyncKeyState(NUM_4):
            current_weapon_index = prev_weapon(weapons_list, current_weapon_index)
            print(weapons_list[current_weapon_index]['name'])
            time.sleep(0.2)
        if win32api.GetAsyncKeyState(NUM_6):
            current_weapon_index = next_weapon(weapons_list, current_weapon_index)
            print(weapons_list[current_weapon_index]['name'])
            time.sleep(0.2)
        if is_lmb_pressed() and no_recoil and cursor():
            process_no_recoil(weapons_list, current_weapon_index, no_recoil)
        time.sleep(0.01)


if __name__ == "__main__":
    # if len(sys.argv) < 2 or (len(sys.argv) == 2 and sys.argv[1] == "help"):
    #     print("Usage: python " + sys.argv[0] + " <weapons_data_filename>")
    #     print("Example: python " + sys.argv[0] + " apex")
    # else:
    data_filename = "apex"
    main(data_filename)
