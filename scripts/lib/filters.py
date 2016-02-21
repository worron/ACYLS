# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

import os
import imp
import base
import re

from lxml import etree
from copy import deepcopy
from gi.repository import Gtk, Gdk


class FilterParameter:
	"""Helper to find, change, save and restore certain value in xml tag attrubute.
	Used to work with svg filter parameters.
	"""
	def __init__(self, tag, attr, pattern, repl):
		self.tag = tag
		self.attr = attr
		self.pattern = pattern
		self.repl = repl

		self.remember()

	def match(self, gn=1):
		"""Get current value"""
		match = re.search(self.pattern, self.tag.attrib[self.attr])
		return match.group(gn)

	def set_value(self, value):
		"""Set value"""
		string = self.repl % value
		self.tag.attrib[self.attr] = re.sub(self.pattern, string, self.tag.attrib[self.attr])

	def remember(self):
		"""Remember current value"""
		self.last = self.match(gn=0)

	def restore(self):
		"""Restore last remembered value"""
		self.tag.attrib[self.attr] = re.sub(self.pattern, self.last, self.tag.attrib[self.attr])


class SimpleFilterBase:
	"""Base class for simple filter with fixes parameters."""
	def __init__(self, sourse_path):
		self.group = "General"
		self.is_custom = False
		self.path = sourse_path
		self.fstore = os.path.join(sourse_path, "filter.xml")
		self.load()

	def load(self):
		"""Load filter from xml file"""
		self.tree = etree.parse(self.fstore, base.parser)
		self.root = self.tree.getroot()
		filter_tag = self.root.find(".//*[@id='acyl-filter']")
		visual_tag = self.root.find(".//*[@id='acyl-visual']")

		self.dull = dict(filter=deepcopy(filter_tag), visual=deepcopy(visual_tag))

	def save(self):
		"""Save current model back to xml file"""
		self.root.replace(self.root.find(".//*[@id='acyl-filter']"), deepcopy(self.dull['filter']))
		self.root.replace(self.root.find(".//*[@id='acyl-visual']"), deepcopy(self.dull['visual']))
		self.tree.write(self.fstore, pretty_print=True)

	def get(self):
		"""Return a dict with filter tag and visual tag"""
		return self.dull


class CustomFilterBase(SimpleFilterBase):
	"""Base class for advanced filter with custimizible parametrs"""
	render = None

	def __new__(cls, *args, **kargs):
		if CustomFilterBase.render is None:
			raise NotImplementedError(
				"Attribbute 'render' of 'CustomFilterBase' should be defined before subclass init")
		return object.__new__(cls, *args, **kargs)

	def __init__(self, sourse_path):
		SimpleFilterBase.__init__(self, sourse_path)
		self.is_custom = True
		self.param = dict()
		self.gui = dict()

	def gui_load(self, gui_elements):
		"""Load filter setting GUI from glade file"""
		self.builder = Gtk.Builder()
		self.builder.add_from_file(os.path.join(self.path, "gui.glade"))
		self.builder.connect_signals(self)
		self.gui = {name: self.builder.get_object(name) for name in gui_elements}

		# May cause exeption but should be catched by FilterCollector
		self.gui['window'].set_property("title", "ACYL Filter - %s" % self.name)

	def gui_setup(self):
		raise NotImplementedError("Method 'gui_setup' 'CustomFilterBase' should be defined in subclass")

	# GUI handlers
	def on_apply_click(self, *args):
		CustomFilterBase.render.run(False, forced=True)

	def on_save_click(self, *args):
		for parameter in self.param.values():
			parameter.remember()

		CustomFilterBase.render.run(False, forced=True)
		if 'window' in self.gui: self.gui['window'].hide()

		self.save()

	def on_cancel_click(self, *args):
		for parameter in self.param.values():
			parameter.restore()

		self.gui_setup()
		CustomFilterBase.render.run(False, forced=True)

	def on_close_window(self, *args):
		if 'window' in self.gui: self.gui['window'].hide()
		return True

	# GUI setup helpers
	def gui_settler_plain(self, *parameters, translate=float):
		"""GUI setup helper - simple parameters"""
		for parameter in parameters:
			self.gui[parameter].set_value(translate(self.param[parameter].match()))

	def gui_settler_color(self, button, color, alpha=None):
		"""GUI setup helper - color"""
		rgba = Gdk.RGBA()
		rgba.parse(self.param[color].match())
		if alpha is not None: rgba.alpha = float(self.param[alpha].match())
		self.gui[button].set_rgba(rgba)

	# Handler generators
	def build_plain_handler(self, *parameters, translate=None):
		"""Function factory.
		New handler changing simple filter parameter according GUI scale widget.
		"""
		def change_handler(widget):
			value = widget.get_value()
			if translate is not None: value = translate(value)
			for parameter in parameters:
				self.param[parameter].set_value(value)
			self.render.run(False)

		return change_handler

	def build_color_handler(self, color, alpha=None):
		"""Function factory.
		New handler changing color filter parameter according GUI colorbutton widget.
		"""
		def change_handler(widget):
			rgba = widget.get_rgba()
			if alpha is not None:
				self.param[alpha].set_value(rgba.alpha)
				rgba.alpha = 1  # dirty trick
			self.param[color].set_value(rgba.to_string())
			self.render.run(False, forced=True)

		return change_handler


class FilterCollector(base.ItemPack):
	"""Object to load, store and switch between acyl-filters"""
	def __init__(self, path, filename='filter.py', dfilter='Disabled', dgroup='General'):
		self.default_filter = dfilter
		self.default_group = dgroup
		self.groups = dict()

		for root, _, files in os.walk(path):
			if filename in files:
				try:
					module = imp.load_source(filename.split('.')[0], os.path.join(root, filename))
					filter_ = module.Filter()
					self.add(filter_)
				except Exception as e:
					print("Fail to load filter from %s" % root)
					print(str(e))

		self.groupnames = list(self.groups.keys())
		self.groupnames.sort(key=lambda key: 1 if key == self.default_group else 2)
		self.set_group(self.groupnames[0])

	def add(self, filter_):
		"""Add new filter to collection"""
		group = filter_.group
		if group in self.groups:
			self.groups[group].update({filter_.name: filter_})
		else:
			self.groups[group] = {filter_.name: filter_}

	def set_group(self, group):
		"""Select filter group"""
		self.pack = self.groups[group]
		self.build_names(sortkey=lambda key: 1 if key == self.default_filter else 2)

	def get_group_index(self, name):
		"""Get group index by filter name"""
		for group, names in self.groups.items():
			if name in names: return self.groupnames.index(group)
		else:
			return 0


class RawFilterEditor:
	def load_xml(self, file_):
		self.xmlfile = file_
		self.tree = etree.parse(self.xmlfile, base.parser)
		self.root = self.tree.getroot()
		self.source = etree.tostring(self.root, pretty_print=True).decode("utf-8")

	def get_updated_preview(self):
		svgroot = etree.fromstring(self.preview, base.parser)
		XHTML = "{%s}" % svgroot.nsmap[None]
		old_filter_tag = svgroot.find(".//%s*[@id='acyl-filter']" % XHTML)
		old_visual_tag = svgroot.find(".//%s*[@id='acyl-visual']" % XHTML)
		old_filter_tag.getparent().replace(old_filter_tag, deepcopy(self.filter_tag))
		old_visual_tag.getparent().replace(old_visual_tag, deepcopy(self.visual_tag))
		new_prewiew = etree.tostring(svgroot, pretty_print=True)
		return new_prewiew

	def get_source(self):
		return self.source

	def load_source(self, text):
		root = etree.fromstring(text, base.parser)
		self.source = etree.tostring(root, pretty_print=True).decode("utf-8")

		self.filter_tag = root.find(".//*[@id='acyl-filter']")
		self.visual_tag = root.find(".//*[@id='acyl-visual']")

	def load_preview(self, file_):
		with open(file_, 'rb') as f: self.preview = f.read()
		self.load_source(self.preview)
