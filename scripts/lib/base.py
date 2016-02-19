# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
"""Shared functions and vars for ACYLS simple modules collected here."""

import os
from lxml import etree

# Define lxml parser here
parser = etree.XMLParser(remove_blank_text=True)


class IconFinder:
	"""SVG icon seach"""
	@staticmethod
	def get_svg_all(*dirlist):
		"""Find all SVG icon in directories"""
		filelist = []
		for path in dirlist:
			for root, _, files in os.walk(path):
				filelist.extend([os.path.join(root, name) for name in files if name.endswith('.svg')])
		return filelist

	@staticmethod
	def get_svg_first(*dirlist):
		"""Find first SVG icon in directories"""
		for path in dirlist:
			for root, _, files in os.walk(path):
				for filename in files:
					if filename.endswith('.svg'): return os.path.join(root, filename)


class ItemPack:
	"""Base for work with groups of items"""
	def switch(self, name):
		"""Set current item by name"""
		if name in self.pack:
			self.current = self.pack[name]

	def build_names(self, sortkey):
		"""Build sorted list of item names and set active first"""
		self.names = [key for key in self.pack]
		self.names.sort(key=sortkey)
		self.current = self.pack[self.names[0]]
