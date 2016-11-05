# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import os
from gi.repository import Gtk
from gi.repository.GdkPixbuf import Pixbuf

import acyls
from acyls.lib.fssupport import Miner
from acyls.lib.guisupport import PixbufCreator, TreeViewHolder
from acyls.lib.multithread import multithread


class ApplicationsPage:
	"""Icon view GUI"""
	def __init__(self, config):
		self.active = None

		# Create object for iconview
		self.iconminer = Miner(config.getdir("Directories", "applications"))

		# Read icon size settins from config
		self.VIEW_ICON_SIZE = config.getint("PreviewSize", "group")

		# Load GUI
		self.builder = Gtk.Builder()
		self.builder.add_from_file(os.path.join(acyls.dirs['gui'], "applications.glade"))

		gui_elements = (
			'apps_grid', 'applications_combo', 'icons_view', 'path_label',
		)
		self.gui = {element: self.builder.get_object(element) for element in gui_elements}

		# Build store
		self.store = Gtk.ListStore(Pixbuf)
		self.gui['icons_view'].set_model(self.store)
		self.gui['icons_view'].set_pixbuf_column(0)
		self.iconminer_lock = TreeViewHolder(self.gui['icons_view'])

		# Fill up GUI
		for name in self.iconminer.group.keys():
			self.gui['applications_combo'].append_text(name)

		# connect signals
		self.gui['applications_combo'].connect("changed", self.on_applications_combo_changed)

		# setup
		self.gui['applications_combo'].set_active(0)

		# Mainpage buttnons hanlers
		self.mhandlers = dict()
		self.bhandlers = dict()
		self.mhandlers['apply_button'] = self.on_apply_click

	# GUI handlers
	@multithread
	def on_applications_combo_changed(self, combo):
		DIG_LEVEL = 1
		text = combo.get_active_text()
		if text and text in self.iconminer.group:
			self.active = text
			self.gui['path_label'].set_text(self.iconminer.group[text]["path"])
			self.iconminer.dig(self.iconminer.group[text]["directory"], DIG_LEVEL)

			icons = self.iconminer.get_icons(DIG_LEVEL)
			pixbufs = [PixbufCreator.new_single_at_size(icon, self.VIEW_ICON_SIZE) for icon in icons]

			# GUI action catched in seperate function and moved to main thread
			def update_gui_with_new_icons():
				with self.iconminer_lock:
					self.store.clear()
					for pix in pixbufs:
						self.store.append([pix])

			return update_gui_with_new_icons

	def on_page_switch(self):
		self.gui['applications_combo'].emit("changed")

	def on_apply_click(self, *args):
		self.iconminer.send_group(self.active)
