#!/usr/bin/env python3
# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

import os
import sys

if sys.version_info < (3, 0):
	sys.stdout.write("Requires Python 3.x\n")
	sys.exit(1)

import configparser
from gi.repository import Gtk, Gdk, GLib
from copy import deepcopy
import threading

import common
# import lib
from lib.pixbuf import PixbufCreator

DIRS = dict(
	user = "data/user",
	default = "data/default"
)


def load_gtk_css(file_):
	style_provider = Gtk.CssProvider()
	style_provider.load_from_path(file_)

	Gtk.StyleContext.add_provider_for_screen(
		Gdk.Screen.get_default(),
		style_provider,
		Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
	)


class ACYL:
	lock = threading.Lock()

	def spinner(handler):
		"""Multithread decorator"""
		def action(*args, **kwargs):
			with ACYL.lock:
				inst = args[0]
				inst.gui['window'].get_window().set_cursor(Gdk.Cursor(Gdk.CursorType.WATCH))
				try:
					post_process_action = handler(*args, **kwargs)
					GLib.idle_add(on_done, post_process_action)
				except Exception as e:
					print("Error in multithreading:\n%s" % str(e))
				finally:
					inst.gui['window'].get_window().set_cursor(None)

		def on_done(post_process_action):
			if callable(post_process_action): post_process_action()

		def wrapper(*args, **kwargs):
			thread = threading.Thread(target=action, args=args, kwargs=kwargs)
			thread.daemon = True
			thread.start()

		return wrapper

	def __init__(self):
		# Set config files manager
		self.keeper = common.FileKeeper(DIRS['default'], DIRS['user'])

		# Helpers
		self.iconchanger = common.IconChanger()

		# Config file setup
		self.configfile = self.keeper.get("config.ini")
		self.config = configparser.ConfigParser()
		self.config.read(self.configfile)

		# Set data file for saving icon render settings
		# Icon render setting will stored for every icon group separately
		self.dbfile = self.keeper.get("store.acyl")
		self.database = common.DataStore(self.dbfile)

		# File dialog
		self.filechooser = common.FileChooser(DIRS['user'])

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
		# Load filters from certain directory
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
		self.pageindex = 0

		self.PREVIEW_ICON_SIZE = int(self.config.get("PreviewSize", "single"))
		self.VIEW_ICON_SIZE = int(self.config.get("PreviewSize", "group"))

		# Colors store index
		self.HEXCOLOR = 0
		self.ALPHA = 1
		self.OFFSET = 2
		self.RGBCOLOR = 3

		# ACTIVATE GUI
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
			self.write_gui_settings_to_base(['filter'])

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
				pixbuf = PixbufCreator.new_single_at_size(icon, self.VIEW_ICON_SIZE)
				self.gui['alt_icon_store'].append([pixbuf])

	@spinner
	def on_iconview_combo_changed(self, combo):
		DIG_LEVEL = 1
		text = combo.get_active_text()
		if text:
			self.iconview.dig(text.lower(), DIG_LEVEL)

			icons = self.iconview.get_icons(DIG_LEVEL)
			pixbufs = [PixbufCreator.new_single_at_size(icon, self.VIEW_ICON_SIZE) for icon in icons]

			# Because of trouble with Gtk threading
			# Heavy GUI action catched in seperate function and moved to main thread
			# Should be fixed if possible
			def update_gui_with_new_icons():
				self.gui['iconview_store'].clear()
				for pix in pixbufs: self.gui['iconview_store'].append([pix])

			return update_gui_with_new_icons

	def on_gradient_type_switched(self, combo):
		self.gradient.set_tag(combo.get_active_text())
		self.write_gui_settings_to_base(['gradtype'])
		self.read_gui_setting_from_base(['gradtype', 'direction'])

	def on_page_changed(self, nb, page, page_index):
		COLORS, ALTERNATIVES, ICONVIEW = 0, 1, 2
		self.pageindex = page_index
		self.gui['refresh_button'].set_sensitive(page_index == COLORS and not self.render.is_allowed)
		self.gui['apply_button'].set_sensitive(page_index in (COLORS, ALTERNATIVES))

		if page_index == ALTERNATIVES:
			self.gui['alt_theme_combo'].emit("changed")
		elif page_index == ICONVIEW:
			self.gui['iconview_combo'].emit("changed")

	def on_close_window(self, *args):
		self.database.clear(self.icongroups.names)
		self.database.close()

		with open(self.configfile, 'w') as configfile:
			self.config.write(configfile)

		Gtk.main_quit(*args)

	def on_refresh_click(self, *args):
		self.render.run(forced=True)

	def on_filter_settings_click(self, widget, data=None):
		self.filters.current.gui['window'].show_all()

	def on_icongroup_combo_changed(self, combo):
		self.write_gui_settings_to_base()
		files = self.icongroups.current.get_test()
		self.iconchanger.rebuild(*files, **self.current_state())

		self.icongroups.switch(combo.get_active_text())
		self.icongroups.current.cache()

		if self.icongroups.current.is_custom:
			self.gui['custom_icons_store'].clear()
			for key, value in self.icongroups.current.state.items():
				self.gui['custom_icons_store'].append([key.capitalize(), value])

		self.gui['custom_icon_tree_view'].set_sensitive(self.icongroups.current.is_custom)

		self.read_gui_setting_from_base()
		self.preview_update()

	def on_offset_structure_changed(self, model, *args):
		if self.database.get_key(self.icongroups.current.name, 'autooffset'):
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
		self.write_gui_settings_to_base(['autooffset'])

		if self.database.get_key(self.icongroups.current.name, 'autooffset'):
			self.set_offset_auto()

		self.gui['offset_scale'].set_value(self.gui['color_list_store'][self.color_selected][self.OFFSET])
		self.render.run()

	def on_offset_value_changed(self, scale):
		offset = scale.get_value()
		self.gui['color_list_store'].set_value(self.color_selected, self.OFFSET, int(offset))
		self.render.run()

	def on_color_change(self, *args):
		rgba = self.gui['color_selector'].get_current_rgba()
		self.gui['color_list_store'].set_value(self.color_selected, self.HEXCOLOR, PixbufCreator.hex_from_rgba(rgba))
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
		hexcolor = PixbufCreator.hex_from_rgba(rgba)
		self.gui['color_list_store'].append([hexcolor, rgba.alpha, 100, rgba.to_string()])

	def on_remove_offset_button_click(self, *args):
		if len(self.gui['color_list_store']) > 1:
			self.gui['color_list_store'].remove(self.color_selected)

	def on_copy_settings_button_click(self, *args):
		self.state_buffer = deepcopy(self.database.get_dump(self.icongroups.current.name))

	def on_paste_settings_button_click(self, *args):
		self.database.update(self.icongroups.current.name, self.state_buffer)
		self.read_gui_setting_from_base()

	def on_reset_settings_button_click(self, *args):
		self.database.reset(self.icongroups.current.name)
		self.read_gui_setting_from_base()

	def on_save_settings_button_click(self, *args):
		is_ok, file_ = self.filechooser.save()
		if is_ok: self.database.save_to_file(file_)

	def on_open_settings_button_click(self, *args):
		is_ok, file_ = self.filechooser.load()
		if is_ok:
			self.database.load_from_file(file_)
			self.read_gui_setting_from_base()

	@spinner
	def on_apply_click(self, *args):
		if self.pageindex == 0:
			files = self.icongroups.current.get_real()
			self.iconchanger.rebuild(*files, **self.current_state())
		else:
			self.alternatives.send_icons(2, self.config.get("Directories", "real"))

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
		self.read_gui_setting_from_base()
		self.fullrefresh(savedata=False)

		# Restore curtain GUI elements state from last session
		self.gui['rtr_button'].set_active(self.config.getboolean("Settings", "autorender"))

	def current_state(self):
		"""Get current icon settings"""
		return dict(
			gradient=self.gradient,
			gfilter=self.filters.current,
			data=self.database.get_dump(self.icongroups.current.name)
		)

	def fullrefresh(self, savedata=True):
		"""Refresh icon preview and update database if needed"""
		if not self.is_preview_locked:
			if savedata: self.write_gui_settings_to_base()
			state = self.current_state()
			self.icongroups.current.preview = self.iconchanger.rebuild_text(self.icongroups.current.preview, **state)
			self.preview_update()

	def read_gui_setting_from_base(self, keys=None):
		"""Read settings from file and set GUI according it"""
		self.is_preview_locked = True

		keys = keys if keys is not None else self.database.setkeys
		dump = self.database.get_dump(self.icongroups.current.name)

		if 'colors' in keys:
			self.gui['color_list_store'].clear()
			for color in dump['colors']:
				self.gui['color_list_store'].append(color)

		if 'direction' in keys:
			self.gui['direction_list_store'].clear()
			for coord in dump['direction'][self.gradient.tag]:
				self.gui['direction_list_store'].append(coord)

		if 'autooffset' in keys:
			self.gui['offset_switch'].set_active(not dump['autooffset'])

		if 'gradtype' in keys:
			self.gui['gradient_combo'].set_active(common.Gradient.profiles[dump['gradtype']]['index'])

		if 'filter' in keys:
			filter_ = dump['filter']
			self.gui['filter_group_combo'].set_active(self.filters.get_group_index(filter_))

			filter_index = self.filters.names.index(filter_) if filter_ in self.filters.names else 0
			self.gui['filters_combo'].set_active(filter_index)

		self.is_preview_locked = False
		self.fullrefresh(savedata=False)

	def write_gui_settings_to_base(self, keys=None):
		"""Write settings to file"""
		keys = keys if keys is not None else self.database.setkeys
		dump = self.database.get_dump(self.icongroups.current.name)

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

	def preview_update(self):
		"""Update icon preview"""
		if self.icongroups.current.is_double:
			icon1, icon2 = self.icongroups.current.preview, self.icongroups.current.pair
			if self.icongroups.current.pairsw:
				icon1, icon2 = icon2, icon1

			pixbuf = PixbufCreator.new_double_at_size(icon1, icon2, size=self.PREVIEW_ICON_SIZE)
		else:
			pixbuf = PixbufCreator.new_single_at_size(self.icongroups.current.preview, self.PREVIEW_ICON_SIZE)

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

if __name__ == "__main__":
	os.chdir(os.path.dirname(os.path.abspath(__file__)))
	load_gtk_css('themefix.css')
	main = ACYL()
	Gtk.main()
