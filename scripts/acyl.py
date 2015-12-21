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

DIRS = dict(
	main = {name: "../scalable/" + name + "_icons" for name in ("real", "alternative")},
	data = {'current': "data/current", 'default': "data/default"},
	filters = "filters",
	preview = {name: "preview/" + name for name in ("main", "unknown", "custom")}
)

class PixbufCreator(GdkPixbuf.Pixbuf):
	"""Advanced pixbuf"""
	def new_double_from_files_at_size(*files, size):
		"""Merge two icon in one"""
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
		return GdkPixbuf.Pixbuf.new_from_file_at_size(file_, size, size)

class ColorSelectWrapper:

	def __init__(self, selector):
		self.selector = selector

	def get_hex_color(self):
		rgba = self.selector.get_current_rgba()
		color = "#%02X%02X%02X" % tuple([getattr(rgba, name) * 255 for name in ("red", "green", "blue")])
		# color = "#" + "%02X" % (rgba.red * 255) + "%02X" % (rgba.green * 255) + "%02X" % (rgba.blue * 255)
		return color, rgba.alpha

	def set_hex_color(self, color, alpha):
		rgba = [int(c, 16) / 255.0 for c in [color[i:i+2] for i in range(1, 7, 2)]] + [alpha]
		# rgba = (int(color[1:3], 16) / 255.0, int(color[3:5], 16) / 255.0, int(color[5:7], 16) / 255.0, alpha)
		self.selector.set_current_rgba(Gdk.RGBA(*rgba))


class ACYL:
	def __init__(self):
		self.builder = Gtk.Builder()
		self.builder.add_from_file('gui.glade')

		self.keeper = common.FileKeeper(DIRS['data']['default'], DIRS['data']['current'])

		self.configfile = self.keeper.get("config")
		self.config = configparser.ConfigParser()
		self.config.read(self.configfile)

		self.preview_file = tempfile.NamedTemporaryFile(dir="/tmp", prefix="tempsvg")

		self.dbfile = self.keeper.get("store")
		self.db = shelve.open(self.dbfile)

		self.iconview = common.Prospector(DIRS['main']['real'])
		self.alternatives = common.Prospector(DIRS['main']['alternative'])

		self.icongroups = common.IconGroupCollector(self.config)

		common.CustomFilterBase.connect_refresh(self.on_refresh_click)
		self.filters = common.FilterCollector(DIRS['filters'])

		self.gradient = common.Gradient()

		gui_elements = (
			'window', 'preview_icon', 'offset_list_store', 'offset_tree_view', 'direction_list_store',
			'offset_scale', 'offset_switch', 'alt_group_combo', 'alt_theme_combo', 'gradient_combo',
			'filters_combo', 'iconview_combo', 'icongroup_combo', 'alt_icon_store', 'iconview_store',
			'custom_icon_tree_view', 'refresh_button', 'filter_settings_button', 'apply_button',
			'custom_icons_store', 'color_selector', 'notebook'
		)

		self.gui = {element: self.builder.get_object(element) for element in gui_elements}
		self.color_selector_wr = ColorSelectWrapper(self.gui['color_selector'])

		self.gui['window'].show_all()

		self.offset_selected = None
		self.preview_icon_size = int(self.config.get("PreviewSize", "single"))
		self.view_icon_size = int(self.config.get("PreviewSize", "group"))
		self.icongroups.current.cache_preview(self.preview_file)
		self.autooffset = False
		self.current_page_index = 0
		self.is_preview_locked = False
		self.is_rtr_allowed = False

	# GUI handlers
	def on_rtr_toggled(self, switch, *args):
		self.is_rtr_allowed = switch.get_active()
		self.gui['refresh_button'].set_sensitive(not self.is_rtr_allowed)
		self.on_refresh_click()

	def on_filter_combo_changed(self, combo):
		self.filters.switch(combo.get_active_text())
		self.gui['filter_settings_button'].set_sensitive(self.filters.current.is_custom)
		self.database_write(['filter'])
		self.change_icon(self.preview_file.name)
		self.preview_update()

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
				pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon, self.view_icon_size, self.view_icon_size)
				self.gui['alt_icon_store'].append([pixbuf])

	def on_iconview_combo_changed(self, combo):
		DIG_LEVEL = 1
		text = combo.get_active_text()
		if text:
			self.iconview.dig(text.lower(), DIG_LEVEL)
			self.gui['iconview_store'].clear()

			for icon in self.iconview.get_icons(DIG_LEVEL):
				pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon, self.view_icon_size, self.view_icon_size)
				self.gui['iconview_store'].append([pixbuf])

	def on_gradient_type_switched(self, combo):
		self.gradient.set_tag(combo.get_active_text())
		self.database_write(['gradtype'])
		self.database_read(['gradtype', 'direction'])

	def on_page_changed(self, nb, page, page_index):
		self.gui['refresh_button'].set_sensitive(page_index == 0 and not self.is_rtr_allowed)
		self.gui['apply_button'].set_sensitive(page_index in (0, 1))
		self.current_page_index = page_index

	def on_close_window(self, *args):
		self.preview_file.close()
		for key in filter(lambda key: key != 'default' and key not in self.icongroups.names, self.db.keys()):
			del self.db[key]
			print("Key %s was removed from data store" % key)
		self.db.close()
		Gtk.main_quit(*args)

	def change_icon(self, *files):
		common.IconChanger.rebuild(
			*files,
			gradient=self.gradient,
			gfilter = self.filters.current,
			data = self.db.get(self.icongroups.current.name, self.db['default'])
		)

	def on_refresh_click(self, *args):
		if not self.is_preview_locked:
			self.database_write()
			self.change_icon(self.preview_file.name)
			self.preview_update()

	def on_apply_click(self, widget, data=None):
		if self.current_page_index == 0:
			files = self.icongroups.current.get_real()
			self.change_icon(*files)
		else:
			self.alternatives.send_icons(2, DIRS['main']['real'])

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
		if self.autooffset:
			self.set_offset_auto()

		if len(model) > 0:
			self.gui['offset_tree_view'].set_cursor(len(model) - 1)
			self.gui['offset_scale'].set_value(model[len(model) - 1][2]) # fix this!!!

	def on_offset_selection_changed(self, selection):
		model, sel = selection.get_selected()

		if sel:
			self.offset_selected = sel
			color = model[sel][0]
			alpha = model[sel][1]
			self.color_selector_wr.set_hex_color(color, alpha)

			offset = model[sel][2]
			self.gui['offset_scale'].set_value(offset)

	def on_autooffset_toggled(self, switch, *args):
		is_active = switch.get_active()
		self.gui['offset_scale'].set_sensitive(is_active)
		self.autooffset = not is_active

		if self.autooffset:
			self.set_offset_auto()

		self.gui['offset_scale'].set_value(self.gui['offset_list_store'][self.offset_selected][2])
		self.real_time_render()

	def on_offset_value_changed(self, scale):
		offset = scale.get_value()
		self.gui['offset_list_store'].set_value(self.offset_selected, 2, int(offset))
		self.real_time_render()

	def on_color_change(self, *args):
		color, alpha = self.color_selector_wr.get_hex_color()
		self.gui['offset_list_store'].set_value(self.offset_selected, 0, color)
		self.gui['offset_list_store'].set_value(self.offset_selected, 1, alpha)
		self.real_time_render()

	def on_direction_edited(self, widget, path, text):
		self.gui['direction_list_store'][path][1] = int(text)
		self.real_time_render()

	def on_custom_icon_toggled(self, widget, path):
		self.gui['custom_icons_store'][path][1] = not self.gui['custom_icons_store'][path][1]
		name = self.gui['custom_icons_store'][path][0].lower()
		self.icongroups.current.switch_state(name)
		self.icongroups.current.cache_preview(self.preview_file)

		self.real_time_render()
		self.preview_update()

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

		#GUI setup finished, now update all slave elements
		self.database_read()
		self.change_icon(self.preview_file.name)
		self.preview_update()

	def database_read(self, keys=['direction', 'colors', 'filter', 'autooffset', 'gradtype']):
		"""Read data from file and set GUI according it"""
		self.is_preview_locked = True

		section = self.icongroups.current.name if self.icongroups.current.name in self.db else 'default'

		if 'colors' in keys:
			self.gui['offset_list_store'].clear()
			for color in self.db[section]['colors']:
				self.gui['offset_list_store'].append(color)

		if 'direction' in keys:
			self.gui['direction_list_store'].clear()
			for coord in self.db[section]['direction'][self.gradient.tag]:
				self.gui['direction_list_store'].append(coord)

		if 'autooffset' in keys:
			self.autooffset = self.db[section]['autooffset']
			self.gui['offset_switch'].set_active(not self.autooffset)

		if 'gradtype' in keys:
			self.gui['gradient_combo'].set_active(self.gradient.profile['index'])

		if 'filter' in keys:
			filter_ = self.db[section]['filter']
			self.gui['filters_combo'].set_active(self.filters.names.index(filter_) if filter_ in self.filters.names else 0)

		self.is_preview_locked = False
		self.change_icon(self.preview_file.name)
		self.preview_update()

	def database_write(self, keys=['direction', 'colors', 'filter', 'autooffset', 'gradtype']):
		"""Write data to file"""
		section = self.icongroups.current.name

		if section not in self.db:
			self.db[section] = deepcopy(self.db['default'])

		dump = self.db[section]

		if 'gradtype' in keys:
			dump['gradtype'] = self.gradient.tag
		if 'autooffset' in keys:
			dump['autooffset'] = self.autooffset
		if 'filter' in keys:
			dump['filter'] = self.gui['filters_combo'].get_active_text()
		if 'colors' in keys:
			dump['colors'] = [list(row) for row in self.gui['offset_list_store']]
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

			pixbuf = PixbufCreator.new_double_from_files_at_size(icon1, icon2, size=self.preview_icon_size)
		else:
			pixbuf = PixbufCreator.new_single_from_file_at_size(self.preview_file.name, size=self.preview_icon_size)

		self.gui['preview_icon'].set_from_pixbuf(pixbuf)

	def real_time_render(self):
		if self.is_rtr_allowed:
			self.on_refresh_click()

	def add_offset_line(self, *args):
		color, alpha = self.color_selector_wr.get_hex_color()
		self.gui['offset_list_store'].append([color, alpha, 100])

	def remove_offset_line(self, *args):
		if len(self.gui['offset_list_store']) > 1:
			self.gui['offset_list_store'].remove(self.offset_selected)

	def set_offset_auto(self):
		rownum = len(self.gui['offset_list_store'])
		if rownum > 1:
			step = 100 / (rownum - 1)
			for i, row in enumerate(self.gui['offset_list_store']):
				row[2] = i * step
		elif rownum == 1:
			self.gui['offset_list_store'][0][2] = 100

if __name__ == "__main__":
	main = ACYL()
	main.fill_up_gui()

	Gtk.main()
