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
        self.log("Unable to handle fight right now", LogType.Error)
        print('\a')
        print('\007')
        self.click(data.Boxes('Fight Button Light'))
        while self.wait_for_box_appear(box_name='Fight Button Light', timeout=0.5) or \
              self.wait_for_box_appear(box_name='Fight Button Dark', timeout=0.5):
            self.log("Still in fight", LogType.Info)
            if self.wait_for_box_appear(box_name='Fight Button Dark', timeout=0.5):
                self.sleep(0.5)
                self.log("Waiting for our turn to play", LogType.Info)
            else:
                screen_initial = np.asarray(tools.screen_game(data.Boxes['Whole Screen']))
                self.click(data.KeyboardShortcuts(arakne))
                self.sleep(0.5)
                screen_spell = np.asarray(tools.screen_game(data.Boxes['Whole Screen']))
                difference_screen = screen_initial - screen_spell
                np.nonzero(difference_screen)


