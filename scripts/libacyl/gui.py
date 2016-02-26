# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

import os
from gi.repository import GdkPixbuf, Gio, GLib, Gtk


DIALOGS_PROFILE = dict(
	save = (
		"Save ACYL settings", None, Gtk.FileChooserAction.SAVE,
		(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
	),
	load = (
		"Load ACYL settings from file", None, Gtk.FileChooserAction.OPEN,
		(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
	)
)


class FileChooser:
	"""File selection helper based on Gtk file dialog"""
	def build_dialog_action(name):
		def action(self):
			response = self.dialogs[name].run()
			file_ = self.dialogs[name].get_filename()

			self.dialogs[name].hide()
			self.dialogs[name].set_current_folder(self.dialogs[name].get_current_folder())

			return response == Gtk.ResponseType.OK, file_
		return action

	def __init__(self, start_folder, default_name):
		self.dialogs = dict()
		for name, args in DIALOGS_PROFILE.items():
			self.dialogs[name] = Gtk.FileChooserDialog(*args)
			self.dialogs[name].set_current_folder(start_folder)

		self.dialogs['save'].set_current_name(default_name)

	load = build_dialog_action('load')
	save = build_dialog_action('save')


class PixbufCreator():
	"""Advanced pixbuf creator"""
	@classmethod
	def new_double_at_size(cls, *icons, size):
		"""Merge two icon in one pixbuf"""
		pixbuf = [cls.new_single_at_size(icon, size) for icon in icons]

		GdkPixbuf.Pixbuf.composite(
			pixbuf[1], pixbuf[0],
			0, 0,
			size, size,
			size / 2, size / 2,
			0.5, 0.5,
			GdkPixbuf.InterpType.BILINEAR,
			255)

		return pixbuf[0]

	@staticmethod
	def new_single_at_size(icon, size):
		"""Alias for creatinng pixbuf from file or string at size"""
		if os.path.isfile(icon):
			pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon, size, size)
		else:
			stream = Gio.MemoryInputStream.new_from_bytes(GLib.Bytes.new(icon))
			pixbuf = GdkPixbuf.Pixbuf.new_from_stream_at_scale(stream, size, size, True)
		return pixbuf

	@staticmethod
	def hex_from_rgba(rgba):
		"""Translate color from Gdk.RGBA to html hex format"""
		return "#%02X%02X%02X" % tuple([int(getattr(rgba, name) * 255) for name in ("red", "green", "blue")])


class ActionHandler:
	"""Small helper to control an action"""
	def __init__(self, action, is_allowed=False):
		self.action = action
		self.is_allowed = is_allowed

	def set_state(self, state):
		"""Allow/block action"""
		self.is_allowed = state

	def run(self, *args, forced=False):
		"""Try to action"""
		if self.is_allowed or forced:
			self.action(*args)
