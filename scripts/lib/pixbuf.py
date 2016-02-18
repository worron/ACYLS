# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

import os
from gi.repository import GdkPixbuf, Gio, GLib


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
		return "#%02X%02X%02X" % tuple([getattr(rgba, name) * 255 for name in ("red", "green", "blue")])
