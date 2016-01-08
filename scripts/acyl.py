#!/usr/bin/env python3

import sys, os
if sys.version_info < (3, 0):
	sys.stdout.write("Requires Python 3.x\n")
	sys.exit(1)

os.chdir(os.path.dirname(os.path.abspath(__file__)))

import shelve
import configparser
from gi.repository import Gtk, Gdk
from copy import deepcopy

import common

style_provider = Gtk.CssProvider()
style_provider.load_from_path('themefix.css')

Gtk.StyleContext.add_provider_for_screen(
	Gdk.Screen.get_default(),
	style_provider,
	Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)

DIRS = dict(data = {'current': "data/current", 'default': "data/default"})

class ACYL:
	def __init__(self):
		# Set config files manager
		self.keeper = common.FileKeeper(DIRS['data']['default'], DIRS['data']['current'])

		# Helpers
		self.pixcreator = common.PixbufCreator()
		self.iconchanger = common.IconChanger()

		# Config file setup
		self.configfile = self.keeper.get("config")
		self.config = configparser.ConfigParser()
		self.config.read(self.configfile)

		# Set data file for saving icon render settings
		# Icon render setting will stored for every icon group separately
		self.dbfile = self.keeper.get("store")
		self.db = shelve.open(self.dbfile)

		# Create objects for alternative and real icon full prewiew
		self.iconview = common.Prospector(self.config.get("Directories", "real"))
		self.alternatives = common.Prospector(self.config.get("Directories", "alternatives"))

		# Load icon groups from config file
		self.icongroups = common.IconGroupCollector(self.config)
		self.icongroups.current.cache()

		# Create object for preview render control
		self.render = common.ActionHandler(self.fullrefresh)
		# Connect preview render controller to filters class
		common.CustomFilterBase.render = self.render
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
			'custom_icons_store', 'color_selector', 'notebook', 'rtr_button', 'filter_group_combo'
		)

		self.gui = {element: self.builder.get_object(element) for element in gui_elements}

		# Other
		self.color_selected = None
		self.state_buffer = None
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

	def on_filter_group_combo_changed(self, combo):
		group = combo.get_active_text()
		self.filters.set_group(group)

		self.gui['filters_combo'].remove_all()
		for name in self.filters.names:
			self.gui['filters_combo'].append_text(name)

		if not self.is_preview_locked:
			self.gui['filters_combo'].set_active(0)

	def on_filter_combo_changed(self, combo):
		name = combo.get_active_text()
		if name is not None:
			self.filters.switch(name)
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
				pixbuf = self.pixcreator.new_single_at_size(icon, self.VIEW_ICON_SIZE)
				self.gui['alt_icon_store'].append([pixbuf])

	def on_iconview_combo_changed(self, combo):
		DIG_LEVEL = 1
		text = combo.get_active_text()
		if text:
			self.iconview.dig(text.lower(), DIG_LEVEL)
			self.gui['iconview_store'].clear()

			for icon in self.iconview.get_icons(DIG_LEVEL):
				pixbuf = self.pixcreator.new_single_at_size(icon, self.VIEW_ICON_SIZE)
				self.gui['iconview_store'].append([pixbuf])

	def on_gradient_type_switched(self, combo):
		self.gradient.set_tag(combo.get_active_text())
		self.database_write(['gradtype'])
		self.database_read(['gradtype', 'direction'])

	def on_page_changed(self, nb, page, page_index):
		COLORS, ALTERNATIVES, ICONVIEW = 0, 1, 2
		apply_action = self.apply_colors if page_index == COLORS else self.apply_alternatives
		self.gui['apply_button'].connect("clicked", apply_action)
		self.gui['refresh_button'].set_sensitive(page_index == COLORS and not self.render.is_allowed)
		self.gui['apply_button'].set_sensitive(page_index in (COLORS, ALTERNATIVES))

		if page_index == ALTERNATIVES:
			self.gui['alt_theme_combo'].emit("changed")
		elif page_index == ICONVIEW:
			self.gui['iconview_combo'].emit("changed")

	def on_close_window(self, *args):
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
		self.iconchanger.rebuild(*files, **self.current_state())

		self.icongroups.switch(combo.get_active_text())
		self.icongroups.current.cache()

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
		self.icongroups.current.cache()

		self.render.run(forced=True)

	def on_add_offset_button_click(self, *args):
		rgba = self.gui['color_selector'].get_current_rgba()
		hexcolor = self.hex_from_rgba(rgba)
		self.gui['color_list_store'].append([hexcolor, rgba.alpha, 100, rgba.to_string()])

	def on_remove_offset_button_click(self, *args):
		if len(self.gui['color_list_store']) > 1:
			self.gui['color_list_store'].remove(self.color_selected)

	def on_copy_settings_button_click(self, *args):
		self.state_buffer = deepcopy(self.db[self.icongroups.current.name])

	def on_paste_settings_button_click(self, *args):
		self.db[self.icongroups.current.name] = deepcopy(self.state_buffer)
		self.database_read()

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

		# Filter groups
		for group in self.filters.groupnames:
			self.gui['filter_group_combo'].append_text(group)
		# self.gui['filter_group_combo'].set_active(0)

		# gradient type list
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

		# Restore curtain GUI elements state from last session
		self.gui['rtr_button'].set_active(self.config.getboolean("Settings", "autorender"))

	def current_state(self):
		"""Get current icon settings"""
		return dict(
			gradient=self.gradient,
			gfilter=self.filters.current,
			data=self.db.get(self.icongroups.current.name, self.db['default'])
		)

	def apply_colors(self, *args):
		"""Function for apply button on color GUI page"""
		files = self.icongroups.current.get_real()
		self.iconchanger.rebuild(*files, **self.current_state())

	def apply_alternatives(self, *args):
		"""Function for apply button on alternatives GUI page"""
		self.alternatives.send_icons(2, self.config.get("Directories", "real"))

	def fullrefresh(self, savedata=True):
		"""Refresh icon preview and update data if needed"""
		if not self.is_preview_locked:
			if savedata: self.database_write()
			state = self.current_state()
			self.icongroups.current.preview = self.iconchanger.rebuild_text(self.icongroups.current.preview, **state)
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
			self.gui['gradient_combo'].set_active(common.Gradient.profiles[self.db[section]['gradtype']]['index'])

		if 'filter' in keys:
			filter_ = self.db[section]['filter']
			self.gui['filter_group_combo'].set_active(self.filters.get_group_index(filter_))

			filter_index = self.filters.names.index(filter_) if filter_ in self.filters.names else 0
			self.gui['filters_combo'].set_active(filter_index)

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
			icon1, icon2 = self.icongroups.current.preview, self.icongroups.current.pair
			if self.icongroups.current.pairsw:
				icon1, icon2 = icon2, icon1

			pixbuf = self.pixcreator.new_double_at_size(icon1, icon2, size=self.PREVIEW_ICON_SIZE)
		else:
			pixbuf = self.pixcreator.new_single_at_size(self.icongroups.current.preview, self.PREVIEW_ICON_SIZE)

		self.gui['preview_icon'].set_from_pixbuf(pixbuf)

	def set_offset_auto(self):
		"""Set fair offset for all colors in gradient"""
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
