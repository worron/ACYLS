# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import os
from gi.repository import Gtk
from gi.repository.GdkPixbuf import Pixbuf

import libacyl
from libacyl.fs import Prospector
from libacyl.gui import PixbufCreator, TreeViewHolder
from libacyl.multithread import multithread


class ViewerPage:
	"""Icon view GUI"""
	def __init__(self, config):
		self.config = config
		self.bhandlers = dict()
		self.mhandlers = dict()

		# Create object for iconview
		self.iconview = Prospector(self.config.get("Directories", "real"))

		# Read icon size settins from config
		self.VIEW_ICON_SIZE = int(config.get("PreviewSize", "group"))

		# Load GUI
		self.builder = Gtk.Builder()
		self.builder.add_from_file(os.path.join(libacyl._dirs['gui'], "viewer.glade"))

		gui_elements = (
			'iconview_grid', 'iconview_combo', 'icons_view',
		)
		self.gui = {element: self.builder.get_object(element) for element in gui_elements}

		# Build store
		self.store = Gtk.ListStore(Pixbuf)
		self.gui['icons_view'].set_model(self.store)
		self.gui['icons_view'].set_pixbuf_column(0)
		self.iconview_lock = TreeViewHolder(self.gui['icons_view'])

		# Fill up GUI
		for name in self.iconview.structure[0]['directories']:
			self.gui['iconview_combo'].append_text(name.capitalize())

		# connect signals
		self.gui['iconview_combo'].connect("changed", self.on_iconview_combo_changed)

		# setup
		self.gui['iconview_combo'].set_active(0)

	# GUI handlers
	@multithread
	def on_iconview_combo_changed(self, combo):
		DIG_LEVEL = 1
		text = combo.get_active_text()
		if text:
			self.iconview.dig(text.lower(), DIG_LEVEL)

			icons = self.iconview.get_icons(DIG_LEVEL)
			pixbufs = [PixbufCreator.new_single_at_size(icon, self.VIEW_ICON_SIZE) for icon in icons]

			# GUI action catched in seperate function and moved to main thread
			def update_gui_with_new_icons():
				with self.iconview_lock:
					self.store.clear()
					for pix in pixbufs:
						self.store.append([pix])

			return update_gui_with_new_icons

	def on_page_switch(self):
		self.gui['iconview_combo'].emit("changed")
