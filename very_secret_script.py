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
    weapons_list = []
    current_weapon_index = 0

    if not weapon_filename:
        print("WARNING: Filename with weapons data was not set! Meh!?")
        return weapons_list, current_weapon_index

    weapon_filepath = "./weapon_data/{}.json".format(weapon_filename)

    try:
        with open(weapon_filepath) as f:
            weapons_data = json.load(f)
    except:
        print("ERROR: Can not open/read file with weapon data. No file? Corrupted? WTF!?")
        print("INFO: Since last error I will use default EMPTY_WEAPONS_LIST. Go check your data files, okay?")
        return weapons_list, current_weapon_index
    
    weapons_list = weapons_data

    for i, weapon in enumerate(weapons_list):
        if weapon["name"]:
            image = load_image_from_file(f"./weapon_data/apex_img/{weapon['name']}.png")
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



def get_tick(rpm):
    rps = rpm/60
    mstick = 1000.0/rps
    stick = round(mstick/1000, 3)
    return stick


def process_no_recoil( weapons_list, current_weapon_index, no_recoil):
    shot_index = 1
    prev_x = 0
    prev_y = 0
    time_points = weapons_list[current_weapon_index]["time_points"]
    prev_time = 0
    mx = weapons_list[current_weapon_index]["x"]
    my = weapons_list[current_weapon_index]["y"]
    t = 0
    start = time.time()
    while is_lmb_pressed():
        if t < time.perf_counter():
            if shot_index < len(mx):
                dx = -(mx[shot_index] - prev_x)/1.5 #/INGAME SENSE!!!!
                dy = -(my[shot_index] - prev_y)/1.5 #/INGAME SENSE!!!!
                prev_x = mx[shot_index]
                prev_y = my[shot_index]
                mouse_move_relative(dx, dy)
                # print(shot_index,round((time.time() - start)*1000),time_points[shot_index]-prev_time)
                t = time.perf_counter() + (time_points[shot_index]-prev_time)/1000
                # print(time.time() - start)
                prev_time = time_points[shot_index]
                start = time.time()
                shot_index += 1



def fit_resolution(area):
    result = []
    for point in area:
        result.append(point * 1.33333333333333)
    return result

def detect_current_weapon(weapons_list):
    image_to_check = get_screen_area_as_image([1570, 960, 1700, 1000])
    for index, weapon in enumerate(weapons_list):
        if weapon["image"] is not None:
            found_xy = search_image_in_image(weapon["image"], image_to_check)
            if found_xy:
                return index
    return None


def main(weapon_filename):
    running = True
    no_recoil = True
    weapons_list, current_weapon_index = load_weapons(weapon_filename)
    detected = None

    while running:
        if win32api.GetAsyncKeyState(KEY_1) or win32api.GetAsyncKeyState(KEY_2):
            time.sleep(0.2)
            detected = detect_current_weapon(weapons_list)
            if detected is not None: print(weapons_list[detected]['name'], end='                      \r')
            else: print('no recoil', end='                      \r')
            current_weapon_index = detected

        if win32api.GetAsyncKeyState(F4):
            no_recoil = toggle_recoil(no_recoil)
            time.sleep(0.2)
        if win32api.GetAsyncKeyState(F10):
            running = not running
            beep_exit()
            print("INFO: Exiting!")
            time.sleep(0.5)
        if is_lmb_pressed() and no_recoil and cursor() and detected is not None:
            process_no_recoil( weapons_list, current_weapon_index, no_recoil)
        time.sleep(0.01)



if __name__ == "__main__":

    data_filename = "specs"
    main(data_filename)
