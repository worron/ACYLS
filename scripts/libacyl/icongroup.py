# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

import os
import libacyl.fs as fs
import libacyl.base as base
from itertools import count
from libacyl.gui import PixbufCreator


class BasicIconGroup:
	"""Object with fixed list of real and preview pathes for icon group"""
	def __init__(self, name, emptydir, testdirs, realdirs, pairdir=None, pairsw=False, index=0):
		self.name = name
		self.index = index
		self.emptydir = emptydir
		self.testdirs = testdirs
		self.realdirs = realdirs
		self.is_custom = False
		self.is_double = pairdir is not None
		self.pairsw = pairsw

		if self.is_double:
			self.pair = fs.get_svg_first(pairdir)

		self.cache_preview()

	def cache_preview(self):
		"""Save current preview icon as text"""
		preview_icon = fs.get_svg_first(*self.testdirs)
		if not preview_icon:
			preview_icon = fs.get_svg_first(self.emptydir)

		with open(preview_icon, 'rb') as f:
			self.preview = f.read()

	def get_preview_pixbuf(self, icon_size):
		"""Create icongroup preview pixbuf"""
		if self.is_double:
			icon1, icon2 = self.preview, self.pair
			if self.pairsw:
				icon1, icon2 = icon2, icon1

			pixbuf = PixbufCreator.new_double_at_size(icon1, icon2, size=icon_size)
		else:
			pixbuf = PixbufCreator.new_single_at_size(self.preview, size=icon_size)

		return pixbuf

	def get_real(self):
		"""Get list of all real icons for group"""
		return fs.get_svg_all(*self.realdirs)

	def get_test(self):
		"""Get list of all testing icons for group"""
		return fs.get_svg_all(*self.testdirs)


class CustomIconGroup(BasicIconGroup):
	"""Object with customizible list of real and preview pathes for icon group"""
	def __init__(self, name, emptydir, testbase, realbase, pairdir=None, pairsw=False, index=0):
		BasicIconGroup.__init__(self, name, emptydir, [], [], pairdir, pairsw, index)
		self.is_custom = True
		self.testbase = testbase
		self.realbase = realbase
		self.state = dict.fromkeys(next(os.walk(testbase))[1], False)

	def switch_state(self, subgroup):
		"""Ebable/disable one of the subgroup by name"""
		self.state[subgroup] = not self.state[subgroup]
		self.testdirs = [os.path.join(self.testbase, name) for name in self.state if self.state[name]]
		self.realdirs = [os.path.join(self.realbase, name) for name in self.state if self.state[name]]
		self.cache_preview()


class IconGroupCollector(base.ItemPack):
	"""Object to load, store and switch between icon groups"""
	def __init__(self, config):
		self.pack = dict()
		counter = count(1)

		while True:
			index = next(counter)
			section = "IconGroup" + str(index)
			if not config.has_section(section):
				break
			try:
				# group type
				is_custom = config.getboolean(section, 'custom')

				# plain text arguments
				args = ("name", "pairdir", "emptydir", "testbase", "realbase")
				kargs = {k: config.get(section, k) for k in args if config.has_option(section, k)}

				# list type arguments
				args_l = ("testdirs", "realdirs")
				kargs_l = {k: config.get(section, k).split(";") for k in args_l if config.has_option(section, k)}

				# boolean type arguments
				args_b = ("pairsw",)
				kargs_b = {k: config.getboolean(section, k) for k in args_b if config.has_option(section, k)}

				for d in (kargs_l, kargs_b):
					kargs.update(d)
				kargs['index'] = index

				self.pack[kargs['name']] = CustomIconGroup(**kargs) if is_custom else BasicIconGroup(**kargs)
			except Exception:
				print("Fail to load icon group №%d" % index)

		self.build_names(sortkey=lambda name: self.pack[name].index)
