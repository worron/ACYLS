# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

import shutil
import re
import os
import sys
import imp
import shelve

from gi.repository import Gtk, GdkPixbuf, Gio, GLib, Gdk
from copy import deepcopy
from lxml import etree
from itertools import count


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
		if self.is_allowed or forced: self.action(*args)


class DataStore:
	"""Shelve database handler"""
	def __init__(self, dbfile, dsection='default'):
		self.db = shelve.open(dbfile, writeback=True)
		self.dsection = dsection
		self.setkeys = list(self.db[dsection].keys())

	def get_dump(self, section):
		if section not in self.db: self.db[section] = deepcopy(self.db[self.dsection])
		return self.db[section]

	def update(self, section, data):
		self.db[section] = deepcopy(data)

	def reset(self, section):
		self.db[section] = deepcopy(self.db[self.dsection])

	def get_key(self, section, key):
		return self.db[section][key]

	def save_to_file(self, dbfile):
		try:
			with shelve.open(dbfile) as newdb:
				for key in self.db: newdb[key] = self.db[key]
		except Exception as e:
			print("Fail to save settings to file:\n%s" % str(e))

	def load_from_file(self, dbfile):
		try:
			with shelve.open(dbfile) as newdb:
				for key in newdb: self.db[key] = newdb[key]
		except Exception as e:
			print("Fail to load settings from file:\n%s" % str(e))

	def clear(self, current_groups):
		for section in filter(lambda key: key != self.dsection and key not in current_groups, self.db.keys()):
			del self.db[section]

	def close(self):
		self.db.close()
