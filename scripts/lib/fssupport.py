# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
"""ACYLS functiont to work with file system"""

import os
import shutil
import configparser

from itertools import count


def get_svg_all(*dirlist):
	"""Find all SVG icon in directories"""
	filelist = []
	for path in dirlist:
		for root, _, files in os.walk(path):
			filelist.extend([os.path.join(root, name) for name in files if name.endswith('.svg')])
	return filelist


def get_svg_first(*dirlist):
	"""Find first SVG icon in directories"""
	for path in dirlist:
		for root, _, files in os.walk(path):
			for filename in files:
				if filename.endswith('.svg'):
					return os.path.join(root, filename)


def _is_dir(item):
	"""Check if given item has valid fs path"""
	if isinstance(item, list):
		return all((_is_dir(e) for e in item))
	else:
		return os.path.isdir(item)


def _read_icon_group_data(config, index, section):
	"""Read icon group data from config section"""
	# plain text arguments
	args = ("name", "pairdir", "emptydir", "testbase", "realbase")
	kargs = {k: config.get(section, k) for k in args if config.has_option(section, k)}

	# list type arguments
	args_l = ("testdirs", "realdirs")
	kargs_l = {k: config.get(section, k).split(";") for k in args_l if config.has_option(section, k)}

	# boolean type arguments
	args_b = ("pairsw", "custom")
	kargs_b = {k: config.getboolean(section, k) for k in args_b if config.has_option(section, k)}

	# collect it all together
	for d in (kargs_l, kargs_b):
		kargs.update(d)
		kargs['index'] = index

	# check directories
	for key in (k for k in kargs.keys() if k not in ("custom", "index", "name", "pairsw")):
		if not _is_dir(kargs[key]):
			raise FileNotFoundError()

	return kargs


class ConfigReader:
	"""Custom config parser"""
	def double_config_action(method):
		def action(self, section, option):
			try:
				res = getattr(self.mainconfig, method)(section, option)
			except Exception as e:
				print(self.base_error_message % (section, option, e))
				res = getattr(self.backconfig, method)(section, option)
			return res
		return action

	def direct_action(method):
		def action(self, *args):
			return getattr(self.mainconfig, method)(*args)
		return action

	def __init__(self, main_dir, backup_dir, filename):
		self.userfile = os.path.join(main_dir, filename)
		systemfile = os.path.join(backup_dir, filename)

		if not os.path.isfile(self.userfile) and os.path.isfile(systemfile):
			shutil.copy(systemfile, main_dir)

		self.mainconfig = configparser.ConfigParser()
		self.mainconfig.read(self.userfile)

		self.backconfig = configparser.ConfigParser()
		self.backconfig.read(systemfile)

		self.base_error_message = (
			"Fail to read user config section '%s' option '%s'\n%s\n"
			"Trying to get value from backup config\n"
		)

	get = double_config_action("get")
	getint = double_config_action("getint")
	getboolean = double_config_action("getboolean")

	set = direct_action("set")
	has_option = direct_action("has_option")
	has_section = direct_action("has_section")

	def getdir(self, section, option):
		"""Get directory from config"""
		try:
			res = self.mainconfig.get(section, option)
			if not os.path.isdir(res):
				raise FileNotFoundError("Directory '%s' was not found" % res)
		except Exception as e:
			print(self.base_error_message % (section, option, e))
			res = self.backconfig.get(section, option)
		return res

	def build_icon_groups(self, simple_group_class, custom_group_class, from_backup=False):
		"""Read all available icon group data from config"""
		pack = {}
		counter = count(1)
		config = self.backconfig if from_backup else self.mainconfig

		while True:
			index = next(counter)
			section = "IconGroup" + str(index)
			if not config.has_section(section):
				break
			try:
				group = _read_icon_group_data(config, index, section)
				is_custom = group.pop("custom")
				pack[group['name']] = custom_group_class(**group) if is_custom else simple_group_class(**group)
			except Exception as e:
				print("Fail to load icon group №%d\n%s" % (index, e))

		return pack

	def write(self):
		"""Write user config file"""
		with open(self.userfile, 'w') as configfile:
			self.mainconfig.write(configfile)


class Prospector:
	""""Find icons on diffrent deep level in directory tree"""
	def __init__(self, root):
		self.root = root
		self.structure = {0: dict(zip(('root', 'directories'), next(os.walk(root))))}

	def dig(self, name, level):
		"""Choose active directory on given level"""
		if level - 1 in self.structure and name in self.structure[level - 1]['directories']:
			dest = os.path.join(self.structure[level - 1]['root'], name)
			self.structure[level] = dict(zip(('root', 'directories'), next(os.walk(dest))))
			self.structure[level]['directories'].sort()
			self.structure = {key: self.structure[key] for key in self.structure if key <= level}

	def get_icons(self, level):
		"""Get icon list from given level"""
		if level in self.structure:
			return get_svg_all(self.structure[level]['root'])

	def send_icons(self, level, dest):
		"""Merge files form given level to destination place"""
		if level in self.structure:
			source_root_dir = self.structure[level]['root']
			for source_dir, _, files in os.walk(source_root_dir):
				destination_dir = source_dir.replace(source_root_dir, dest)
				for file_ in files:
					shutil.copy(os.path.join(source_dir, file_), destination_dir)
