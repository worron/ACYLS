# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import os
from gi.repository import Gtk
import configparser

# User modules
import libacyl
from libacyl.toolbar import MainToolBar
from libacyl.colorpage import ColorPage
from libacyl.altpage import AlternativesPage
from libacyl.gui import load_gtk_css
from libacyl.fs import FileKeeper
from libacyl.data import DataStore


class MainWindow:
	"""Main window constructor"""
	def __init__(self):
		self.last_button_handlers = dict()

		# Set config files manager
		self.keeper = FileKeeper(libacyl._dirs['default'], libacyl._dirs['user'])

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
		self.builder.add_from_file(os.path.join(libacyl._dirs['gui'], "main.glade"))

		gui_elements = (
			'window', 'notebook', 'exit_button', 'refresh_button', 'maingrid', 'apply_button',
		)
		self.gui = {element: self.builder.get_object(element) for element in gui_elements}
		self.buttons = ('refresh_button', 'apply_button')

		# Add panel
		self.toolbar = MainToolBar()
		self.gui['maingrid'].attach(self.toolbar.gui['toolbar'], 0, 0, 1, 1)

		# Add notebook pages
		self.pages = list()

		# colors
		self.colorpage = ColorPage(self.database, self.config)
		self.gui['notebook'].append_page(self.colorpage.gui['colorgrid'], Gtk.Label('Colors'))
		self.pages.append(self.colorpage)

		# alternatives
		self.altpage = AlternativesPage(self.config)
		self.gui['notebook'].append_page(self.altpage.gui['alternatives_grid'], Gtk.Label('Alternatives'))
		self.pages.append(self.altpage)

		# Connect signals
		self.signals = dict()
		self.gui['window'].connect("delete-event", self.on_close_window)
		self.gui['exit_button'].connect("clicked", self.on_close_window)
		self.gui['notebook'].connect("switch_page", self.on_page_changed)

		self.colorpage.gui['render_button'].connect("toggled", self.on_render_toggled)

		self.toolbar.connect_signals(self.colorpage.bhandlers)

		# Fill up GUI
		load_gtk_css(os.path.join(libacyl._dirs['css'], 'themefix.css'))
		self.gui['notebook'].emit("switch_page", self.colorpage.gui['colorgrid'], 0)
		self.gui['window'].show_all()
		# self.colorpage.gui['colorgrid'].get_window().set_cursor(Gdk.Cursor(Gdk.CursorType.WATCH))

	# GUI handlers
	def on_page_changed(self, nb, page, index):
		self.toolbar.set_buttons_sensitive(self.pages[index].bhandlers)
		for button in self.buttons:
			if button in self.last_button_handlers:
				self.gui[button].disconnect_by_func(self.last_button_handlers[button])
			if button in self.pages[index].mhandlers:
				self.gui[button].connect("clicked", self.pages[index].mhandlers[button])

			self.gui[button].set_sensitive(button in self.pages[index].mhandlers)
		self.last_button_handlers = self.pages[index].mhandlers

		if index == self.pages.index(self.colorpage):
			self.colorpage.gui['render_button'].emit("toggled")

	def on_render_toggled(self, switch, *args):
		self.gui['refresh_button'].set_sensitive(not self.colorpage.rtr)

	def on_close_window(self, *args):
		Gtk.main_quit(*args)
