# Dindo Bot
# Copyright (c) 2018 - 2019 AXeL

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject
from gui.custom import MiniMap
from lib.shared import LogType, DebugLevel, GameVersion
from lib import maps, data, tools, parser
from .farming import FarmingThread

class JobThread(FarmingThread):

	def __init__(self, parent, game_location):
		FarmingThread.__init__(self, parent, game_location)
		self.podbar_enabled = parent.settings['State']['EnablePodBar']
		self.go_to_bank_pod_percentage = parent.settings['State']['GoToBankPodPercentage']
		self.minimap_enabled = parent.settings['State']['EnableMiniMap']
		self.check_resources_color = parent.settings['Farming']['CheckResourcesColor']
		self.auto_close_popups = parent.settings['Farming']['AutoClosePopups']
		self.collection_time = parent.settings['Farming']['CollectionTime']
		self.first_resource_additional_collection_time = parent.settings['Farming']['FirstResourceAdditionalCollectionTime']
		self.game_version = parent.settings['Game']['Version']

	def collect(self, map_name, store_path):
		map_data = parser.parse_data(maps.load(), map_name)
		if map_data:
			# show resources on minimap
			self.update_minimap(map_data, 'Resource', MiniMap.point_colors['Resource'])
			# collect resources
			is_first_resource = True
			for resource in map_data:
				# check for pause or suspend
				self.pause_event.wait()
				if self.suspend: return
				# check resource color
				if not self.check_resource_color(resource):
					# go to next resource
					continue
				# screen game
				screen = tools.screen_game(self.game_location)
				# click on resource
				self.debug("Collecting resource {'x': %d, 'y': %d, 'color': %s}" % (resource['x'], resource['y'], resource['color']))
				self.click(resource)
				if self.game_version == GameVersion.Retro:
					# re-click to validate
					self.click({'x': resource['x'] + 30, 'y': resource['y'] + 40, 'width': resource['width'], 'height': resource['height']})
				# wait before collecting next one
				if is_first_resource:
					is_first_resource = False
					self.sleep(self.first_resource_additional_collection_time) # wait more for 1st resource
				self.sleep(self.collection_time)
				# remove current resource from minimap (index = 0)
				self.remove_from_minimap(0)
				# check for pause or suspend
				self.pause_event.wait()
				if self.suspend: return
				# check for screen change
				self.debug('Checking for screen change')
				if self.monitor_game_screen(tolerance=2.5, screen=screen, timeout=1, wait_after_timeout=False):
					# check for fight
					if self.game_version != GameVersion.Retro and self.wait_for_box_appear(box_name='Fight Button Light', timeout=1):
						self.log('Fight detected! human help wanted..', LogType.Error)
						self.handle_fight()
					elif self.auto_close_popups:
						# it should be a popup (level up, ...)
						self.debug('Closing popup')
						screen = tools.screen_game(self.game_location)
						if self.game_version == GameVersion.Retro:
							self.press_key(data.KeyboardShortcuts['Enter'])
						elif self.wait_for_box_appear(box_name='Job Level Up Popup', timeout=1):
							location = self.get_box_location('Job Level Up Popup')
							self.click(location)
						else:
							self.press_key(data.KeyboardShortcuts['Esc'])
						# wait for popup to close
						self.monitor_game_screen(tolerance=2.5, screen=screen)
					# check for pause or suspend
					self.pause_event.wait()
					if self.suspend: return
				# get pod
				if self.game_version != GameVersion.Retro and \
				   self.get_pod() >= self.go_to_bank_pod_percentage:
					# pod is full, go to store
					# if store_path != 'None':
					# 	self.go_to_store(store_path)
					# else:
					# 	self.pause()
					self.log('Bot is full pod', LogType.Error)
					return 1

	def check_location_color(self, location):
		game_x, game_y, game_width, game_height = self.game_location
		x, y = tools.adjust_click_position(location['x'], location['y'], location['width'], location['height'], game_x, game_y, game_width, game_height)
		color = tools.get_pixel_color(x, y)
		location['color'] = parser.parse_color(location['color'])
		if location['color'] is not None and not tools.color_matches(color, location['color'], tolerance=10):
			return False
		return True

	def check_resource_color(self, resource):
		# check pixel color
		if self.check_resources_color:
			if self.check_location_color(resource):
				self.debug("Ignoring non-matching resource {'x': %d, 'y': %d, 'color': %s}" % (resource['x'], resource['y'], resource['color']))
				# remove current resource from minimap (index = 0)
				self.remove_from_minimap(0)
				return False
		return True

	def get_pod(self):
		self.pause_event.wait()
		if self.suspend: return
		# get podbar color & percentage
		location = self.get_box_location('PodBar')
		screen = tools.screen_game(location)
		color, percentage = tools.get_dominant_color(screen)
		if tools.color_matches(color, data.Colors['Empty PodBar'], tolerance=10):
			percentage = 100.0 - percentage
		# update pod bar
		self.log(f"Pod {percentage}%, color: {color}")
		self.set_pod(percentage)
		return percentage

	def set_pod(self, percentage):
		if self.podbar_enabled:
			self.debug(f"Update PodBar (percentage: {percentage}%)")
			# set podbar value
			GObject.idle_add(self.parent.podbar.set_fraction, percentage / 100.0)

	def update_minimap(self, points, points_name=None, points_color=None):
		if self.minimap_enabled:
			self.debug('Update MiniMap')
			# clear minimap
			GObject.idle_add(self.parent.minimap.clear)
			# update minimap
			GObject.idle_add(self.parent.minimap.add_points, points, points_name, points_color)

	def remove_from_minimap(self, index):
		if self.minimap_enabled:
			self.debug('Remove point from MiniMap (index: %d)' % index)
			GObject.idle_add(self.parent.minimap.remove_point, index)
