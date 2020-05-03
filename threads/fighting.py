# Dindo Bot

import numpy as np
import time
import gi
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
                im.save("difference.jpeg")
                blue_pixels = np.nonzero(difference_screen)
                # We'll try to drop the arakne on left top most blue pixel
                blue_box = {}
                blue_box['x'] = data.Boxes['Whole Screen']['x'] + blue_pixels[0][0]
                blue_box['y'] = data.Boxes['Whole Screen']['y'] + blue_pixels[1][0]
                blue_box['width'] = data.Boxes['Whole Screen']['width']
                blue_box['height'] = data.Boxes['Whole Screen']['height']
                self.click(blue_box)
                self.log(f"Invoked Spider on {blue_box['x']}, {blue_box['y']}")
                self.sleep(2.0)
                self.log("Calling Epee Divine .. ", LogType.Info)
                self.press_key(data.KeyboardShortcuts['epee'])
            else:
                self.sleep(2.0)
                self.log("Waiting for our turn to play", LogType.Info)
            self.log("End while")
        self.log("Game Finished", LogType.Info)

5