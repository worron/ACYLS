# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import os
from gi.repository import Gtk
import configparser

# User modules
from libacyl.toolbar import MainToolBar
from libacyl.colorpage import ColorPage
from libacyl.gui import load_gtk_css
from libacyl.fs import FileKeeper
from libacyl.data import DataStore

# Data directories
DIRS = dict(
	user = "data/user",
	default = "data/default"
)


class MainWindow:
	"""Main window constructor"""
	def __init__(self):
		# Set config files manager
		self.keeper = FileKeeper(DIRS['default'], DIRS['user'])

		# Config file setup
		self.configfile = self.keeper.get("config.ini")
		self.config = configparser.ConfigParser()
		self.config.read(self.configfile)

		# Set data file for saving icon render settings
		# Icon render setting will stored for every icon group separately
		self.dbfile = self.keeper.get("store.acyl")
		self.database = DataStore(self.dbfile)

		# Load GUI
		self.builder = Gtk.Builder()
		self.builder.add_from_file(os.path.join("gui", "main.glade"))

		gui_elements = (
			'window', 'notebook', 'exit_button', 'refresh_button', 'maingrid',
		)
		self.gui = {element: self.builder.get_object(element) for element in gui_elements}

		# Add panel
		self.toolbar = MainToolBar()
		self.gui['maingrid'].attach(self.toolbar.gui['toolbar'], 0, 0, 1, 1)

		# Add notebook pages
		self.colorpage = ColorPage(self.database, self.config)
		self.gui['notebook'].append_page(self.colorpage.gui['colorgrid'], Gtk.Label('Colors'))

		# Connect signals
		self.signals = dict()
		self.gui['window'].connect("delete-event", self.on_close_window)
		self.gui['exit_button'].connect("clicked", self.on_close_window)
		self.gui['refresh_button'].connect("clicked", self.colorpage.on_refresh_click)

		self.colorpage.gui['render_button'].connect("toggled", self.on_render_toggled)

		self.toolbar.connect_signals(self.colorpage.bhandlers)

		# Fill up GUI
		load_gtk_css('themefix.css')
		self.colorpage.gui['render_button'].emit("toggled")
		self.gui['window'].show_all()

	# Support functions

	# GUI handlers
	def on_close_window(self, *args):
		Gtk.main_quit(*args)

	def on_render_toggled(self, switch, *args):
		self.gui['refresh_button'].set_sensitive(not self.colorpage.rtr)
