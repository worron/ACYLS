import sys, os
if sys.version_info < (3, 0):
	sys.stdout.write("Requires Python 3.x")
	sys.exit(1)

import shelve
import tempfile
import configparser
from gi.repository import Gtk, Gdk, GdkPixbuf, GObject
from copy import deepcopy

os.chdir(os.path.dirname(os.path.abspath(__file__)))

import common

style_provider = Gtk.CssProvider()
style_provider.load_from_path('themefix.css')

Gtk.StyleContext.add_provider_for_screen(
	Gdk.Screen.get_default(),
	style_provider,
	Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)

DIRS = dict(data = {'current': "data/current", 'default': "data/default"})

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


class ACYL:
	def __init__(self):
		# Set config files manager
		self.keeper = common.FileKeeper(DIRS['data']['default'], DIRS['data']['current'])

		# Config file setup
		self.configfile = self.keeper.get("config")
		self.config = configparser.ConfigParser()
		self.config.read(self.configfile)

		# Set temporary file for icon preview
		self.preview_file = tempfile.NamedTemporaryFile(dir=self.config.get("Directories", "tmpfs"), prefix="acyl")

		# Set data file for saving icon render settings
		# Icon render setting will stored for every icon group separately
		self.dbfile = self.keeper.get("store")
		self.db = shelve.open(self.dbfile)

		# Create objects for alternative and real icon full prewiew
		self.iconview = common.Prospector(self.config.get("Directories", "real"))
		self.alternatives = common.Prospector(self.config.get("Directories", "alternatives"))

		# Load icon groups from config file
		self.icongroups = common.IconGroupCollector(self.config)
		self.icongroups.current.cache_preview(self.preview_file)

		# Create object for preview render control
		self.render = common.ActionHandler(self.fullrefresh)
		# Connect preview render controller to filters class
		common.CustomFilterBase.set_render(self.render)
		# Load filters from certain  directory
		self.filters = common.FilterCollector(self.config.get("Directories", "filters"))

		# Build griadient object
		self.gradient = common.Gradient()

		# Load GUI
		self.builder = Gtk.Builder()
		self.builder.add_from_file('gui.glade')

		gui_elements = (
			'window', 'preview_icon', 'color_list_store', 'color_tree_view', 'direction_list_store',
			'offset_scale', 'offset_switch', 'alt_group_combo', 'alt_theme_combo', 'gradient_combo',
			'filters_combo', 'iconview_combo', 'icongroup_combo', 'alt_icon_store', 'iconview_store',
			'custom_icon_tree_view', 'refresh_button', 'filter_settings_button', 'apply_button',
			'custom_icons_store', 'color_selector', 'notebook', 'rtr_button'
		)

		self.gui = {element: self.builder.get_object(element) for element in gui_elements}

		# Other
		self.color_selected = None
		self.is_preview_locked = False

		self.PREVIEW_ICON_SIZE = int(self.config.get("PreviewSize", "single"))
		self.VIEW_ICON_SIZE = int(self.config.get("PreviewSize", "group"))

		# Colors store index
		self.HEXCOLOR = 0
		self.ALPHA = 1
		self.OFFSET = 2
		self.RGBCOLOR = 3

		# Activate GUI
		self.gui['window'].show_all()
		self.fill_up_gui()

	# GUI handlers
	def on_rtr_toggled(self, switch, *args):
		self.render.set_state(switch.get_active())
		self.gui['refresh_button'].set_sensitive(not self.render.is_allowed)
		self.config.set("Settings", "autorender", str(self.render.is_allowed))
		self.render.run(forced=True)

	def on_filter_combo_changed(self, combo):
		self.filters.switch(combo.get_active_text())
		self.gui['filter_settings_button'].set_sensitive(self.filters.current.is_custom)
		self.database_write(['filter'])

		self.fullrefresh(savedata=False)

	def on_alt_group_combo_changed(self, combo):
		DIG_LEVEL = 1
		self.alternatives.dig(combo.get_active_text().lower(), DIG_LEVEL)
		self.gui['alt_theme_combo'].remove_all()

		for name in self.alternatives.structure[DIG_LEVEL]['directories']:
			self.gui['alt_theme_combo'].append_text(name.capitalize())

		self.gui['alt_theme_combo'].set_active(0)

	def on_alt_theme_combo_changed(self, combo):
		DIG_LEVEL = 2
		text = combo.get_active_text()
		if text:
			self.alternatives.dig(text.lower(), DIG_LEVEL)
			self.gui['alt_icon_store'].clear()

			for icon in self.alternatives.get_icons(DIG_LEVEL):
				pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon, self.VIEW_ICON_SIZE, self.VIEW_ICON_SIZE)
				self.gui['alt_icon_store'].append([pixbuf])

	def on_iconview_combo_changed(self, combo):
		DIG_LEVEL = 1
		text = combo.get_active_text()
		if text:
			self.iconview.dig(text.lower(), DIG_LEVEL)
			self.gui['iconview_store'].clear()

			for icon in self.iconview.get_icons(DIG_LEVEL):
				pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon, self.VIEW_ICON_SIZE, self.VIEW_ICON_SIZE)
				self.gui['iconview_store'].append([pixbuf])

	def on_gradient_type_switched(self, combo):
		self.gradient.set_tag(combo.get_active_text())
		self.database_write(['gradtype'])
		self.database_read(['gradtype', 'direction'])

	def on_page_changed(self, nb, page, page_index):
		self.gui['apply_button'].connect("clicked", self.apply_colors if page_index == 0 else self.apply_alternatives)
		self.gui['refresh_button'].set_sensitive(page_index == 0 and not self.render.is_allowed)
		self.gui['apply_button'].set_sensitive(page_index in (0, 1))

	def on_close_window(self, *args):
		self.preview_file.close()

		for key in filter(lambda key: key != 'default' and key not in self.icongroups.names, self.db.keys()):
			del self.db[key]
			print("Key %s was removed from data store" % key)
		self.db.close()

		with open(self.configfile, 'w') as configfile:
			self.config.write(configfile)

		Gtk.main_quit(*args)

	def on_refresh_click(self, *args):
		self.render.run(forced=True)

	def on_filter_settings_click(self, widget, data=None):
		self.filters.current.gui['window'].show_all()

	def on_icongroup_combo_changed(self, combo):
		self.database_write()
		files = self.icongroups.current.get_test()
		self.change_icon(*files)

		self.icongroups.switch(combo.get_active_text())
		self.icongroups.current.cache_preview(self.preview_file)

		if self.icongroups.current.is_custom:
			self.gui['custom_icons_store'].clear()
			for key, value in self.icongroups.current.state.items():
				self.gui['custom_icons_store'].append([key.capitalize(), value])

		self.gui['custom_icon_tree_view'].set_sensitive(self.icongroups.current.is_custom)

		self.database_read()
		self.preview_update()

	def on_offset_structure_changed(self, model, *args):
		if self.db[self.icongroups.current.name]['autooffset']:
			self.set_offset_auto()

		if len(model) > 0:
			last = len(model) - 1
			self.gui['color_tree_view'].set_cursor(last)
			self.gui['offset_scale'].set_value(model[last][2])

	def on_color_selection_changed(self, selection):
		model, sel = selection.get_selected()

		if sel is not None:
			self.color_selected = sel
			rgba = Gdk.RGBA()
			rgba.parse(model[sel][self.RGBCOLOR])
			rgba.alpha = model[sel][self.ALPHA]
			self.gui['color_selector'].set_current_rgba(rgba)

			offset = model[sel][self.OFFSET]
			self.gui['offset_scale'].set_value(offset)

	def on_autooffset_toggled(self, switch, *args):
		is_active = switch.get_active()
		self.gui['offset_scale'].set_sensitive(is_active)
		self.database_write(['autooffset'])

		if self.db[self.icongroups.current.name]['autooffset']:
			self.set_offset_auto()

		self.gui['offset_scale'].set_value(self.gui['color_list_store'][self.color_selected][self.OFFSET])
		self.render.run()

	def on_offset_value_changed(self, scale):
		offset = scale.get_value()
		self.gui['color_list_store'].set_value(self.color_selected, self.OFFSET, int(offset))
		self.render.run()

	def on_color_change(self, *args):
		rgba = self.gui['color_selector'].get_current_rgba()
		self.gui['color_list_store'].set_value(self.color_selected, self.HEXCOLOR, self.hex_from_rgba(rgba))
		self.gui['color_list_store'].set_value(self.color_selected, self.ALPHA, rgba.alpha)
		self.gui['color_list_store'].set_value(self.color_selected, self.RGBCOLOR, rgba.to_string())
		self.render.run()

	def on_direction_edited(self, widget, path, text):
		self.gui['direction_list_store'][path][1] = int(text)
		self.render.run()

	def on_custom_icon_toggled(self, widget, path):
		self.gui['custom_icons_store'][path][1] = not self.gui['custom_icons_store'][path][1]
		name = self.gui['custom_icons_store'][path][0].lower()
		self.icongroups.current.switch_state(name)
		self.icongroups.current.cache_preview(self.preview_file)

		self.render.run(forced=True)

	def on_add_offset_button_click(self, *args):
		rgba = self.gui['color_selector'].get_current_rgba()
		hexcolor = self.hex_from_rgba(rgba)
		self.gui['color_list_store'].append([hexcolor, rgba.alpha, 100, rgba.to_string()])

	def on_remove_offset_button_click(self, *args):
		if len(self.gui['color_list_store']) > 1:
			self.gui['color_list_store'].remove(self.color_selected)

	# Support methods
	def fill_up_gui(self):
		"""Fill all dynamic gui elemets"""
		# Set GUI element in 'silent' mode
		# There is no reaction on setup for elements below

		# Custom icon names
		for group in self.icongroups.pack.values():
			if group.is_custom:
				for key, value in group.state.items():
					self.gui['custom_icons_store'].append([key.capitalize(), value])
				break

		# Filters list
		for name in self.filters.names:
			self.gui['filters_combo'].append_text(name)

		# Gradient type list
		for tag in sorted(common.Gradient.profiles):
			self.gui['gradient_combo'].append_text(tag)
		self.gui['gradient_combo'].set_active(0)

		# Icon groups list
		for name in self.icongroups.names:
			self.gui['icongroup_combo'].append_text(name)
		self.gui['icongroup_combo'].set_active(0)

		# Connect gui hanlers now
		self.builder.connect_signals(self)

		# Set GUI element in 'active' mode
		# All elements below will trigger its handlers

		# Alternative icon groups list
		for name in self.alternatives.structure[0]['directories']:
			self.gui['alt_group_combo'].append_text(name.capitalize())
		self.gui['alt_group_combo'].set_active(0)

		# Icon view groups list
		for name in self.iconview.structure[0]['directories']:
			self.gui['iconview_combo'].append_text(name.capitalize())
		self.gui['iconview_combo'].set_active(0)

		# GUI setup finished, now update autogenerated elements which depended on current GUI state
		self.database_read()
		self.fullrefresh(savedata=False)

		self.gui['rtr_button'].set_active(self.config.getboolean("Settings", "autorender"))

	def change_icon(self, *files):
		"""Rebuild given icons according current GUI state"""
		common.IconChanger.rebuild(
			*files,
			gradient=self.gradient,
			gfilter = self.filters.current,
			data = self.db.get(self.icongroups.current.name, self.db['default'])
		)

	def apply_colors(self, *args):
		"""Function for apply button on color GUI page"""
		files = self.icongroups.current.get_real()
		self.change_icon(*files)

	def apply_alternatives(self, *args):
		"""Function for apply button on alternatives GUI page"""
		self.alternatives.send_icons(2, self.config.get("Directories", "real"))

	def fullrefresh(self, savedata=True):
		"""Refresh icon preview and update data if needed"""
		if not self.is_preview_locked:
			if savedata: self.database_write()
			self.change_icon(self.preview_file.name)
			self.preview_update()

	def database_read(self, keys=['direction', 'colors', 'filter', 'autooffset', 'gradtype']):
		"""Read data from file and set GUI according it"""
		self.is_preview_locked = True

		section = self.icongroups.current.name if self.icongroups.current.name in self.db else 'default'

		if 'colors' in keys:
			self.gui['color_list_store'].clear()
			for color in self.db[section]['colors']:
				self.gui['color_list_store'].append(color)

		if 'direction' in keys:
			self.gui['direction_list_store'].clear()
			for coord in self.db[section]['direction'][self.gradient.tag]:
				self.gui['direction_list_store'].append(coord)

		if 'autooffset' in keys:
			self.gui['offset_switch'].set_active(not self.db[section]['autooffset'])

		if 'gradtype' in keys:
			self.gui['gradient_combo'].set_active(self.gradient.profile['index'])

		if 'filter' in keys:
			filter_ = self.db[section]['filter']
			self.gui['filters_combo'].set_active(
				self.filters.names.index(filter_) if filter_ in self.filters.names else 0)

		self.is_preview_locked = False
		self.fullrefresh(savedata=False)

	def database_write(self, keys=['direction', 'colors', 'filter', 'autooffset', 'gradtype']):
		"""Write data to file"""
		section = self.icongroups.current.name

		if section not in self.db:
			self.db[section] = deepcopy(self.db['default'])

		dump = self.db[section]

		if 'gradtype' in keys:
			dump['gradtype'] = self.gradient.tag
		if 'autooffset' in keys:
			dump['autooffset'] = not self.gui['offset_switch'].get_active()
		if 'filter' in keys:
			dump['filter'] = self.gui['filters_combo'].get_active_text()
		if 'colors' in keys:
			dump['colors'] = [list(row) for row in self.gui['color_list_store']]
		if 'direction' in keys:
			dump['direction'][self.gradient.tag] = [list(row) for row in self.gui['direction_list_store']]

		# if 'filtername' in dump: del dump['filtername']
		# self.db['default'] = deepcopy(self.db['Custom'])

		self.db[section] = dump

	def preview_update(self):
		"""Update icon preview"""
		if self.icongroups.current.is_double:
			icon1, icon2 = self.preview_file.name, self.icongroups.current.pair
			if self.icongroups.current.pairsw:
				icon1, icon2 = icon2, icon1

			pixbuf = PixbufCreator.new_double_from_files_at_size(icon1, icon2, size=self.PREVIEW_ICON_SIZE)
		else:
			pixbuf = PixbufCreator.new_single_from_file_at_size(self.preview_file.name, size=self.PREVIEW_ICON_SIZE)

		self.gui['preview_icon'].set_from_pixbuf(pixbuf)

	def set_offset_auto(self):
		"""Calculate fair offset for all colors"""
		rownum = len(self.gui['color_list_store'])
		if rownum > 1:
			step = 100 / (rownum - 1)
			for i, row in enumerate(self.gui['color_list_store']):
				row[self.OFFSET] = i * step
		elif rownum == 1:
			self.gui['color_list_store'][0][self.OFFSET] = 100

	def hex_from_rgba(self, rgba):
		"""Translate color from Gdk.RGBA to html hex format"""
		return "#%02X%02X%02X" % tuple([getattr(rgba, name) * 255 for name in ("red", "green", "blue")])

if __name__ == "__main__":
	main = ACYL()
	Gtk.main()
