# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import threading
from gi.repository import Gdk, GLib

global_threading_lock = threading.Lock()


def set_cursor(object_, cursor=None):
	"""Set cursor for given gui structure if possible"""
	for widget in object_.gui.values():
		try:
			widget.get_window().set_cursor(cursor)
			break
		except Exception:
			pass


def multithread(handler):
	"""Multithread decorator"""
	def action(*args, **kwargs):
		with global_threading_lock:
			try:
				result = handler(*args, **kwargs)
				GLib.idle_add(on_done, result, args[0])
			except Exception as e:
				print("Error in multithreading:\n%s" % str(e))

	def on_done(result, inst):
		set_cursor(inst)
		if callable(result):
			result()

	def wrapper(*args, **kwargs):
		set_cursor(args[0], Gdk.Cursor(Gdk.CursorType.WATCH))

		thread = threading.Thread(target=action, args=args, kwargs=kwargs)
		thread.daemon = True
		thread.start()

	return wrapper
