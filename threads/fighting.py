# Dindo Bot

import numpy as np
import time
import gi
import cv2
import imutils
gi.require_version('Gtk', '3.0')
from gi.repository import GObject
from lib.shared import LogType, DebugLevel
from lib import data, tools, imgcompare, accounts
from .game import GameThread

class FightingThread(GameThread):

    def __init__(self, parent, game_location):
        GameThread.__init__(self, parent, game_location)

    def handle_fight(self):
        print('\a')
        print('\007')
        self.sleep(2.0)
        # Ready to fight
        self.click(data.Locations['Fight Button'])
        self.sleep(3.0)
        # The fight has now started
        self.log("The fight has now started")
        index = 0
        # Detection of whose turn it is
        while self.wait_for_box_appear(box_name='Fight Button Light', timeout=0.1, sleep=0.1) or \
              self.wait_for_box_appear(box_name='Fight Button Dark', timeout=0.1, sleep=0.1):
            self.log("Still in fight", LogType.Info)
            if self.wait_for_box_appear(box_name='Fight Button Light', timeout=0.5, sleep=0.1):
                self.log("Playing ...", LogType.Info)
                screen_initial = np.asarray(tools.screen_game(self.game_location, "screenshot-before"))
                self.press_key(data.KeyboardShortcuts['arakne'])
                self.sleep(2.0)
                screen_spell = np.asarray(tools.screen_game(self.game_location, "screenshot-after"))
                difference_screen = screen_initial - screen_spell
                from PIL import Image
                im = Image.fromarray(difference_screen)
                im.save(f"difference-{index}.jpeg")
                
                image = difference_screen
                resized = imutils.resize(image, width=300)
                ratio = image.shape[0] / float(resized.shape[0])

                # convert the resized image to grayscale, blur it slightly,
                # and threshold it
                gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
                blurred = cv2.GaussianBlur(gray, (5, 5), 0)
                thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY)[1]

                # find contours in the thresholded image and initialize the
                # shape detector
                cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                    cv2.CHAIN_APPROX_SIMPLE)
                cnts = imutils.grab_contours(cnts)
               
                cX = 0
                cY = 0
                # loop over the contours
                for c in cnts:
                    # compute the center of the contour, then detect the name of the
                    # shape using only the contour
                    # print(c)
                    # print(f"min: {np.min(c, axis=0)}")
                    # print(f"max: {np.max(c, axis=0)}")

                    dx = np.max(c, axis=0)[0][0] - np.min(c, axis=0)[0][0]
                    # print(dx)
                    if dx < 12 or dx > 14:
                        continue

                    M = cv2.moments(c)
                    if not M["m00"]:
                        continue
                    cX = int((M["m10"] / M["m00"]) * ratio)
                    cY = int((M["m01"] / M["m00"]) * ratio)
                    
                    # shape += str(cX * cY)
                    # multiply the contour (x, y)-coordinates by the resize ratio,
                    # then draw the contours and the name of the shape on the image
                    c = c.astype("float")
                    c *= ratio
                    c = c.astype("int")
                    cv2.drawContours(image, [c], -1, (0, 255, 0), 2)
                    # cv2.putText(image, shape, (cX, cY), cv2.FONT_HERSHEY_SIMPLEX,
                    # 	0.5, (255, 255, 255), 2)
                    cv2.circle(image, (cX,cY), 1, (255,0,0))

                    im = Image.fromarray(image)
                    im.save(f"processed-{index}.jpeg")
                    index += 1

                blue_box = {}
                blue_box['x'] = cX
                blue_box['y'] = cY
                blue_box['width'] = 900
                blue_box['height'] = 712
                self.click(blue_box)
                self.log(f"Invoked Spider on {blue_box['x']}, {blue_box['y']}")

                self.sleep(2.0)
                self.log("End Turn .. ", LogType.Info)
                self.press_key(data.KeyboardShortcuts['EndTurn'])
            else:
                self.sleep(2.0)
                self.log("Waiting for our turn to play", LogType.Info)
            self.log("End while")
        self.log("Game Finished", LogType.Info)

5