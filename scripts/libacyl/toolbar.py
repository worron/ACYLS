# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import os
from gi.repository import Gtk


class MainToolBar:
	"""Main window constructor"""
	def __init__(self):
		# Load GUI
		self.builder = Gtk.Builder()
		self.builder.add_from_file(os.path.join("gui", "toolbar.glade"))

		gui_elements = (
			'toolbar',
		)
		self.gui = {element: self.builder.get_object(element) for element in gui_elements}

		# Connect signals

	# Support functions

	# GUI handlers
