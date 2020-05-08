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
import pyscreenshot as ImageGrab

class FightingThread(GameThread):

    def __init__(self, parent, game_location):
        GameThread.__init__(self, parent, game_location)
        self.index = 0

    def my_turn_to_play(self):
        return True

    def fight_still_on(self):
        if self.has_box_appeared('Victory') or self.has_box_appeared('Defeat'):
            return False 
        return True

    def handle_fight(self):
        print('\a')
        print('\007')
        self.sleep(2.0)
        # Ready to fight
        self.press_key(data.KeyboardShortcuts['EndTurn'])
        self.sleep(6.0)
        # The fight has now started
        self.log("The fight has now started")
        # Passer son premier tour
        self.press_key(data.KeyboardShortcuts['EndTurn'])

        still_in_fight = True
        while still_in_fight:
            self.log("Still in fight", LogType.Info)
            if self.my_turn_to_play():
                self.log("Playing ...", LogType.Info)
                # Wait a couple seconds before playing
                self.sleep(5.0)

                # check for pause or suspend
                self.pause_event.wait() 
                if self.suspend: return
                
                x, y, width, height = self.game_location
                im = ImageGrab.grab(bbox=(x,y, x+width, y+height), backend='pygdk3')
                screen_initial = np.array(im)
                self.press_key(data.KeyboardShortcuts['arakne'])
                self.sleep(3.0)
                im2 = ImageGrab.grab(bbox=(x,y, x+width, y+height), backend='pygdk3')
                screen_spell = np.array(im2)
                self.sleep(1.0)
                difference_screen = screen_initial - screen_spell
                from PIL import Image
                im = Image.fromarray(difference_screen)
                im.save(f"screenshots/difference-{self.index}.jpeg")
                
                image = difference_screen
                resized = imutils.resize(image, width=300)
                ratio = image.shape[0] / float(resized.shape[0])

                # check for pause or suspend
                self.pause_event.wait()
                if self.suspend: return
                
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
                    dx = np.max(c, axis=0)[0][0] - np.min(c, axis=0)[0][0]
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
                    im.save(f"screenshots/processed-{self.index}.jpeg")
                    self.index += 1
                if not len(cnts):
                    self.debug("No contours found.")
                elif self.fight_still_on():
                    blue_box = {}
                    blue_box['x'] = cX
                    blue_box['y'] = cY
                    blue_box['width'] = 900
                    blue_box['height'] = 704
                    self.click(blue_box)
                    self.debug(f"Invoked Spider on {blue_box['x']}, {blue_box['y']}")

                self.sleep(2.0)
                self.log("End Turn .. ", LogType.Info)
                self.press_key(data.KeyboardShortcuts['EndTurn'])
            else:
                self.sleep(2.0)
                self.log("Waiting for our turn to play", LogType.Info)
            # check for pause or suspend
            self.pause_event.wait()
            if self.suspend: return
            still_in_fight = self.fight_still_on()
        self.log("Game Finished", LogType.Info)
        self.press_key('esc')
        self.sleep(3.0)
