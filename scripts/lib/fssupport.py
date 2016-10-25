# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
"""ACYLS functiont to work with file system"""

import os
import shutil
import configparser


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
