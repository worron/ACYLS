import shutil
import re
import os
import sys
import imp

from gi.repository import Gtk, GdkPixbuf
from copy import deepcopy
from lxml import etree
from itertools import count

class IconFinder:
	"""SVG icon seach"""
	def get_svg_all(self, *dirlist):
		"""Find all SVG icon in directories"""
		filelist = []
		for path in dirlist:
			for root, _, files in os.walk(path):
				filelist.extend([os.path.join(root, name) for name in files if name.endswith('.svg')])
		return filelist

	def get_svg_first(self, *dirlist):
		"""Find first SVG icon in directories"""
		for path in dirlist:
			for root, _, files in os.walk(path):
				for filename in files:
					if filename.endswith('.svg'): return os.path.join(root, filename)

class Parser:
	"""Define lxml parser here"""
	parser = etree.XMLParser(remove_blank_text=True)

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


class SimpleFilterBase(Parser):
	"""Base class for simple filter with fixes parameters."""
	def __init__(self, sourse_path):
		self.group = "General"
		self.is_custom = False
		self.path = sourse_path
		self.fstore = os.path.join(sourse_path, "filter.xml")
		self.load()

	def load(self):
		"""Load filter from xml file"""
		self.tree = etree.parse(self.fstore, self.parser)
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
		return object.__new__(cls,*args,**kargs)

	def __init__(self, sourse_path):
		SimpleFilterBase.__init__(self, sourse_path)
		self.is_custom = True
		self.param = dict()
		self.gui = dict()

	def gui_load(self, gui_elements):
		self.builder = Gtk.Builder()
		self.builder.add_from_file(os.path.join(self.path, "gui.glade"))
		self.builder.connect_signals(self)
		self.gui = {name: self.builder.get_object(name) for name in gui_elements}

	def gui_setup(self):
		raise NotImplementedError("Method 'gui_setup' 'CustomFilterBase' should be defined in subclass")

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

class FilterCollector(ItemPack):
	"""Object to load, store and switch between acyl-filters"""
	def __init__(self, path, filename='filter.py', dfilter='Disabled', dgroup='General'):
		self.default_filter = dfilter
		self.default_group = dgroup
		self.groups = dict()

		for root, _, files in os.walk(path):
			if filename in files:
				try:
					module=imp.load_source(filename.split('.')[0], os.path.join(root, filename))
					filter_ = module.Filter()
					self.add(filter_)
				except Exception:
					print("Fail to load filter from %s" % root)

		self.groupnames = list(self.groups.keys())
		self.groupnames.sort(key=lambda key: 1 if key == self.default_group else 2)
		self.set_group(self.groupnames[0])

	def add(self, filter_):
		group = filter_.group
		if group in self.groups:
			self.groups[group].update({filter_.name: filter_})
		else:
			self.groups[group] = {filter_.name: filter_}

	def set_group(self, group):
		self.pack = self.groups[group]
		self.build_names(sortkey=lambda key: 1 if key == self.default_filter else 2)

	def get_group_index(self, name):
		for group, names in self.groups.items():
			if name in names: return self.groupnames.index(group)
		else:
			return 0

class FileKeeper:
	"""Helper to work with user files.
	Trying to get file from current user directory, copy from backup directory if not found.
	"""
	def __init__(self, bakdir, curdir):
		self.bakdir = bakdir
		self.curdir = curdir

	def get(self, name):
		"""Get file by name"""
		fullname = os.path.join(self.curdir, name)
		if not os.path.isfile(fullname):
			shutil.copy(os.path.join(self.bakdir, name), self.curdir)
		return fullname


class BasicIconGroup(IconFinder):
	"""Object with fixed list of real and preview pathes for icon group"""
	def __init__(self, name, testdirs, realdirs, pairdir=None, pairsw=False, index=0):
		self.name = name
		self.index = index
		self.testdirs = testdirs
		self.realdirs = realdirs
		self.is_custom = False
		self.is_double = pairdir is not None
		self.pairsw = pairsw

		if self.is_double:
			self.pair = self.get_svg_first(pairdir)

	def cache_preview(self, cachefile):
		"""Save current preview icon to temporary file"""
		with open(self.get_preview(), 'rb') as f:
			cachefile.seek(0)
			cachefile.write(f.read())
			cachefile.truncate()

	def get_preview(self):
		"""Get active preview for icon group"""
		return self.get_svg_first(*self.testdirs)

	def get_real(self):
		"""Get list of all real icons for group"""
		return self.get_svg_all(*self.realdirs)

	def get_test(self):
		"""Get list of all testing icons for group"""
		return self.get_svg_all(*self.testdirs)


class CustomIconGroup(BasicIconGroup):
	"""Object with customizible list of real and preview pathes for icon group"""
	def __init__(self, name, emptydir, testbase, realbase, pairdir=None, pairsw=False, index=0):
		BasicIconGroup.__init__(self, name, [], [], pairdir, pairsw, index)
		self.is_custom = True
		self.testbase = testbase
		self.realbase = realbase
		self.emptydir = emptydir
		self.state = dict.fromkeys(next(os.walk(testbase))[1], False)

	def switch_state(self, name):
		"""Ebable/disable one of the subgroup by name"""
		self.state[name] = not self.state[name]

		self.testdirs = [os.path.join(self.testbase, name) for name in self.state if self.state[name]]
		self.realdirs = [os.path.join(self.realbase, name) for name in self.state if self.state[name]]

	def get_preview(self):
		"""Get active preview for icon group"""
		return self.get_svg_first(*self.testdirs if self.testdirs else [self.emptydir])


class IconGroupCollector(ItemPack):
	"""Object to load, store and switch between icon groups"""
	def __init__(self, config):
		self.pack = dict()
		counter = count(1)

		while True:
			index = next(counter)
			section = "IconGroup" + str(index)
			if not config.has_section(section): break
			try:
				# group type
				is_custom = config.getboolean(section, 'custom')

				# plain text arguments
				args = ("name", "pairdir", "emptydir", "testbase", "realbase")
				kargs = {k: config.get(section, k) for k in args if config.has_option(section, k)}

				# list type arguments
				args_l = ("testdirs", "realdirs")
				kargs_l = {k: config.get(section, k).split(";") for k in args_l if config.has_option(section, k)}

				# boolean type  arguments
				args_b = ("pairsw",)
				kargs_b = {k: config.getboolean(section, k) for k in args_b if config.has_option(section, k)}

				for d in (kargs_l, kargs_b): kargs.update(d)
				kargs['index'] = index

				self.pack[kargs['name']] = CustomIconGroup(**kargs) if is_custom else BasicIconGroup(**kargs)
			except Exception:
				print("Fail to load icon group №%d" % index)

		self.build_names(sortkey=lambda name: self.pack[name].index)


class Prospector(IconFinder):
	""""Find icons on diffrent deep level in directory tree"""
	def __init__(self, root):
		self.root = root
		self.structure = {0: dict(zip(('root', 'directories'), next(os.walk(root))))}

	def dig(self, name, level):
		"""Choose active directory on given level"""
		if level-1 in self.structure and name in self.structure[level-1]['directories']:
			dest = os.path.join(self.structure[level-1]['root'], name)
			self.structure[level] = dict(zip(('root', 'directories'), next(os.walk(dest))))
			self.structure[level]['directories'].sort()
			self.structure = {key: self.structure[key] for key in self.structure if key <= level}

	def get_icons(self, level):
		"""Get icon list from given level"""
		if level in self.structure:
			return self.get_svg_all(self.structure[level]['root'])

	def send_icons(self, level, dest):
		"""Merge files form given level to destination place"""
		if level in self.structure:
			source_root_dir = self.structure[level]['root']
			for source_dir, _, files in os.walk(source_root_dir):
				destination_dir = source_dir.replace(source_root_dir, dest)
				for file_ in files:
					shutil.copy(os.path.join(source_dir, file_), destination_dir)


class Gradient:
	"""SVG gradient builder"""
	profiles = dict(
		linearGradient = dict(
			titles = ("StartX", "StartY", "EndX", "EndY"),
			attributes = ('x1', 'y1', 'x2', 'y2'),
			index = 0
		),
		radialGradient = dict(
			titles = ("CenterX", "CenterY", "FocusX", "FocusY", "Radius"),
			attributes = ('cx', 'cy', 'fx', 'fy', 'r'),
			index = 1
		),
	)

	def __init__(self, tag='linearGradient'):
		self.set_tag(tag)

	def set_tag(self, tag):
		"""Set gradient type"""
		if tag in Gradient.profiles:
			self.tag = tag
			self.profile = Gradient.profiles[tag]

	def build(self, data):
		"""Build xml tag"""
		# build attribute for gradient
		attr_list = data['direction'][self.tag]
		attr_persents = ["%d%%" % value for title, value in attr_list]
		attr_dict = dict(zip(self.profile['attributes'], attr_persents))
		attr_dict['id'] = "acyl-gradient"

		# create new gradient tag
		gradient = etree.Element(self.tag, attrib=attr_dict)

		# add colors to gradient tag
		for colordata in data['colors']:
			color, alpha, offset = colordata[:3]
			color_attr = {
				'offset': "%d%%" % offset,
				'style': "stop-color:%s;stop-opacity:%f" % (color, alpha)
			}
			etree.SubElement(gradient, 'stop', attrib=color_attr)

		return gradient


class IconChanger(Parser):
	"""SVG icon corrector"""
	def rebuild(*files, gradient, gfilter, data):
		"""Replace gradient and filter in svg icon file"""
		new_gradient_tag = gradient.build(data)
		new_filter_info = gfilter.get()

		for icon in files:
			tree = etree.parse(icon, IconChanger.parser)
			root = tree.getroot()

			XHTML = "{%s}" % root.nsmap[None]
			# XLINK = "{%s}" % root.nsmap['xlink']

			old_filter_tag = root.find(".//%s*[@id='acyl-filter']" % XHTML)
			old_visual_tag = root.find(".//%s*[@id='acyl-visual']" % XHTML)
			old_filter_tag.getparent().replace(old_filter_tag, new_filter_info['filter'])
			old_visual_tag.getparent().replace(old_visual_tag, new_filter_info['visual'])

			old_gradient_tag = root.find(".//%s*[@id='acyl-gradient']" % XHTML)
			old_gradient_tag.getparent().replace(old_gradient_tag, new_gradient_tag)

			tree.write(icon, pretty_print=True)

class PixbufCreator(GdkPixbuf.Pixbuf):
	"""Advanced pixbuf"""
	def new_double_from_files_at_size(*files, size):
		"""Merge two icon in one pixbuf"""
		pixbuf = [GdkPixbuf.Pixbuf.new_from_file_at_size(f, size, size) for f in files]

		GdkPixbuf.Pixbuf.composite(
			pixbuf[1], pixbuf[0],
			0, 0,
			size, size,
			size / 2, size / 2,
			0.5, 0.5,
			GdkPixbuf.InterpType.BILINEAR,
			255)

		return pixbuf[0]

	def new_single_from_file_at_size(file_, size):
		"""Alias for creatinng pixbuf from file at size"""
		return GdkPixbuf.Pixbuf.new_from_file_at_size(file_, size, size)
