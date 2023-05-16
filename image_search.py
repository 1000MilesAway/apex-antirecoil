import cv2
import numpy as np
import time
from PIL import Image, ImageGrab
from win32api import GetSystemMetrics
import math


def load_image_from_file(image_filename):
    img = Image.open(image_filename)
    img = np.array(img)
    img = img[:, :, ::-1].copy()
    return img


def get_screen_area_as_image(area=(0, 0, GetSystemMetrics(0), GetSystemMetrics(1))):
    screen_width = GetSystemMetrics(0)
    screen_height = GetSystemMetrics(1)

    h_coefficient = screen_height / 1080
    w_coefficient = screen_width / 1920
    # print(h_coefficient, w_coefficient)
    area[0] = int(area[0] * w_coefficient) 
    area[1] = int(area[1] * h_coefficient) 
    area[2] = int(area[2] * w_coefficient) 
    area[3] = int(area[3] * h_coefficient) 

    # h, w = image.shape[:-1]  # height and width of searched image

    # print(area)
    x1 = min(int(area[0]), screen_width)
    y1 = min(int(area[1]), screen_height)
    x2 = min(int(area[2]), screen_width)
    y2 = min(int(area[3]), screen_height)

    # print(screen_height, screen_width)

    search_area = (x1, y1, x2, y2)

    img_rgb = ImageGrab.grab(search_area).convert("RGB")
    img_rgb = np.array(img_rgb)  # convert to cv2 readable format (and to BGR)
    img_rgb = img_rgb[:, :, ::-1].copy()  # convert back to RGB

    # print("sssss")
    # cv2.imwrite("weapon.png", img_rgb)
    # time.sleep(10)

    return img_rgb


class AimBot:
    def __init__(self):
        self.prev_frame = None

    def offset_frame(self, x, y):
        screen_width = GetSystemMetrics(0)
        screen_height = GetSystemMetrics(1)

        # print(x, y)
        offset_x = x #- screen_width/2
        offset_y = y #- screen_height/2
        borders =  (200, 100, screen_width-200, screen_height-100)
        crop_area = (borders[0]-offset_x, borders[1]-offset_y, borders[2]-offset_x, borders[3] - offset_y)

        frame = ImageGrab.grab().crop(crop_area).convert("L")
        return frame




    def proccess_frame(self, x, y):
        time.sleep(0.1)
        frame = np.array(self.offset_frame(x, y))
        if self.prev_frame is None:
            self.prev_frame = frame
            return
        
        
        diff = cv2.absdiff(self.prev_frame, frame) #255- 
        diff[-650:, -1000:] = 0
        # cv2.threshold()
        self.prev_frame = frame
        # zeros = np.zeros((diff.shape[0], diff.shape[1], 3))
        zeros = cv2.cvtColor(diff, cv2.COLOR_GRAY2RGB)

        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        Y, X = np.where(diff>200)
        Z = np.column_stack((X,Y)).astype(np.float32)

        nClusters = 3
        target = None
        screen_center = (diff.shape[1] / 2, diff.shape[0] / 2)
        dists = {}
        if Z.shape[0] >= nClusters:
            ret,label,center=cv2.kmeans(Z,nClusters,None,criteria,10,cv2.KMEANS_RANDOM_CENTERS) 
            
            i = 0
            # print("="*50)
            for x,y in center:
                # print(screen_center)
                dists[i] = (math.dist((x, y), screen_center), (screen_center[0] - x, screen_center[1] - y))
                i += 1
                # print(f'Cluster centre: [{int(x)},{int(y)}]')
                # print(math.dist((x, y), screen_center))
                cv2.drawMarker(zeros, (int(x), int(y)), [0,0,255])


        if dists != {}:
            target = min(dists.items(), key=lambda x: x[1][0])[1][1]
        # print(target)
        # diff[-300:-200][-300:-200] = 255
        cv2.imshow('zeros', zeros)
        # cv2.imshow('diff', diff)

        # time.sleep(0.05)
        return target



def search_image_in_image(small_image, large_image, precision=0.95):
    template = small_image.astype(np.float32)
    img_rgb = large_image.astype(np.float32)
    # print(template.shape)
    # print(img_rgb.shape)


    template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    img_rgb = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)

    res = cv2.matchTemplate(img_rgb, template, cv2.TM_CCOEFF_NORMED)
    # print(res)
    threshold = precision
    loc = np.where(res >= threshold)

    found_positions = list(zip(*loc[::-1]))

    # print("FOUND: {}".format(found_positions))
    return found_positions
