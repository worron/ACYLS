# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

import shelve
from copy import deepcopy


class DataStore:
	"""Shelve database handler"""
	def __init__(self, dbfile, dsection='default'):
		self.db = shelve.open(dbfile, writeback=True)
		self.dsection = dsection
		self.setkeys = list(self.db[dsection].keys())

	def get_dump(self, section):
		"""Get data from given section of base"""
		if section not in self.db: self.db[section] = deepcopy(self.db[self.dsection])
		return self.db[section]

	def update(self, section, data):
		"""Update data in given section"""
		self.db[section] = deepcopy(data)

	def reset(self, section):
		"""Reset given section to default"""
		self.db[section] = deepcopy(self.db[self.dsection])

	def get_key(self, section, key):
		"""Get from given section and key"""
		return self.db[section][key]

	def save_to_file(self, dbfile):
		"""Save current database to file"""
		try:
			with shelve.open(dbfile) as newdb:
				for key in self.db: newdb[key] = self.db[key]
		except Exception as e:
			print("Fail to save settings to file:\n%s" % str(e))

	def load_from_file(self, dbfile):
		"""Load database from file"""
		try:
			with shelve.open(dbfile) as newdb:
				for key in newdb: self.db[key] = newdb[key]
		except Exception as e:
			print("Fail to load settings from file:\n%s" % str(e))

	def clear(self, current_groups):
		"""Remove outdated database sections"""
		for section in filter(lambda key: key != self.dsection and key not in current_groups, self.db.keys()):
			del self.db[section]

	def close(self):
		"""Close database file"""
		self.db.close()
