# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import os
from gi.repository import Gtk

import libacyl


class MainToolBar:
	"""Toolbar constructor"""
	def __init__(self):
		# Load GUI
		self.builder = Gtk.Builder()
		self.builder.add_from_file(os.path.join(libacyl._dirs['gui'], "toolbar.glade"))

		gui_elements = (
			'toolbar', 'add_color_toolbutton', 'remove_color_toolbutton', 'copy_color_toolbutton',
			'paste_color_toolbutton', 'save_settings_toolbutton', 'load_settings_toolbutton',
			'reset_settings_toolbutton',
		)
		self.gui = {element: self.builder.get_object(element) for element in gui_elements}

	# Support functions
	def connect_signals(self, pack):
		"""Connect handlers to panel buttnons"""
		for button, handler in pack.items():
			self.gui[button].connect("clicked", handler)
