import sys, os
if sys.version_info < (3, 0):
	sys.stdout.write("Requires Python 3.x")
	sys.exit(1)

import shelve
import tempfile
import configparser
from gi.repository import Gtk, Gdk, GdkPixbuf, GObject
from copy import deepcopy
from itertools import count

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


class ColorSelectWrapper:

	def __init__(self, selector):
		self.selector = selector

	def get_hex_color(self):
		rgba = self.selector.get_current_rgba()
		color = "#%02X%02X%02X" % tuple([rgba.__getattribute__(name) * 255 for name in ("red", "green", "blue")])
		# color = "#" + "%02X" % (rgba.red * 255) + "%02X" % (rgba.green * 255) + "%02X" % (rgba.blue * 255)
		return color, rgba.alpha

	def set_hex_color(self, color, alpha):
		rgba = [int(c, 16) / 255.0 for c in [color[i:i+2] for i in range(1, 7, 2)]] + [alpha]
		# rgba = (int(color[1:3], 16) / 255.0, int(color[3:5], 16) / 255.0, int(color[5:7], 16) / 255.0, alpha)
		self.selector.set_current_rgba(Gdk.RGBA(*rgba))


class IconGroups:

	def __init__(self, config):
		self.allgroups = dict()
		counter = count(1)

		while True:
			index = next(counter)
			section = "IconGroup" + str(index)
			if not config.has_section(section): break
			try:
				is_custom = config.getboolean(section, 'custom')

				args = ("name", "pairdir", "emptydir", "testbase", "realbase")
				kargs = {k: config.get(section, k) for k in args if config.has_option(section, k)}

				l_args = ("testdirs", "realdirs")
				l_kargs = {k: config.get(section, k).split(";") for k in l_args if config.has_option(section, k)}

				b_args = ("pairsw",)
				b_kargs = {k: config.getboolean(section, k) for k in b_args if config.has_option(section, k)}

				for d in (l_kargs, b_kargs): kargs.update(d)
				kargs['index'] = index

				if is_custom:
					self.allgroups[kargs['name']] = common.CustomIconGroup(**kargs)
				else:
					self.allgroups[kargs['name']] = common.BasicIconGroup(**kargs)
			except Exception:
				print("Fail to load icon group №%d" % index)

		self.names = [key for key in self.allgroups]
		self.names.sort(key=lambda name: self.allgroups[name].index)

		self.current = self.allgroups[self.names[0]]

	def switch(self, name):
		if name in self.allgroups:
			self.current = self.allgroups[name]

class Handler:
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

		self.icongroups = IconGroups(self.config)

		common.CustomFilterBase.connect_refresh(self.on_test_click)
		self.filters = common.FilterGroup(DIRS['filters'])

		self.gradient = common.Gradient()

		self.window = self.builder.get_object('mainwindow')
		self.preview_icon = self.builder.get_object('icon_preview')
		self.offset_list_store = self.builder.get_object('offset_list_store')
		self.offset_tree_view = self.builder.get_object('offset_tree_view')
		self.direction_list_store = self.builder.get_object('direction_list_store')
		self.offset_scale = self.builder.get_object('offset_scale')
		self.offset_switch = self.builder.get_object('offset_switch')
		self.alt_group_combo = self.builder.get_object('alt_group_combo')
		self.alt_theme_combo = self.builder.get_object('alt_theme_combo')
		self.gradient_combo = self.builder.get_object('gradient_combo')
		self.filters_combo = self.builder.get_object('filters_combo')
		self.iconview_combo = self.builder.get_object('iconview_combo')
		self.icongroup_combo = self.builder.get_object('icongroup_combo')
		self.alt_icon_store = self.builder.get_object('alt_icon_store')
		self.iconview_store = self.builder.get_object('iconview_store')
		self.alt_icon_view = self.builder.get_object('alt_icon_view')
		self.iconview_view = self.builder.get_object('iconview_view')
		self.custom_icon_tree_view = self.builder.get_object('custom_group_tree_view')
		self.test_button = self.builder.get_object('test_button')
		self.filter_settings_button = self.builder.get_object('filter_settings_button')
		self.apply_button = self.builder.get_object('apply_button')
		self.custom_icons_store = self.builder.get_object('custom_icons_store')
		self.color_selector_wr = ColorSelectWrapper(self.builder.get_object('color_selector'))

		self.window.show_all()

		self.offset_selected = None
		self.preview_icon_size = int(self.config.get("PreviewSize", "single"))
		self.view_icon_size = int(self.config.get("PreviewSize", "group"))
		self.icongroups.current.cache_preview(self.preview_file)
		self.autooffset = False
		self.current_page_index = 0
		self.is_preview_locked = False
		self.is_rtr_allowed = False

	def fill_up_gui(self):
		for group in self.icongroups.allgroups.values():
			if group.is_custom:
				for key, value in group.state.items():
					self.custom_icons_store.append([key.capitalize(), value])
				break

		for name in self.filters.names:
			self.filters_combo.append_text(name)

		for tag in sorted(common.Gradient.profiles):
			self.gradient_combo.append_text(tag)
		self.gradient_combo.set_active(0)

		for name in self.icongroups.names:
			self.icongroup_combo.append_text(name)
		self.icongroup_combo.set_active(0)

		self.builder.connect_signals(self)

		for name in self.alternatives.structure[0]['directories']:
			self.alt_group_combo.append_text(name.capitalize())
		self.alt_group_combo.set_active(0)

		for name in self.iconview.structure[0]['directories']:
			self.iconview_combo.append_text(name.capitalize())
		self.iconview_combo.set_active(0)

		self.offset_read_from_config()
		self.change_icon(self.preview_file.name)
		self.preview_update()

	def real_time_render(self):
		if self.is_rtr_allowed:
			self.on_test_click()

	def on_rtr_toggled(self, switch, *args):
		self.is_rtr_allowed = switch.get_active()
		self.test_button.set_sensitive(not self.is_rtr_allowed)
		self.on_test_click()

	def on_filter_combo_changed(self, combo):
		self.filters.switch(combo.get_active_text())

		self.filter_settings_button.set_sensitive(self.filters.current.is_custom)

		self.offset_write_to_config()
		self.change_icon(self.preview_file.name)
		self.preview_update()

	def on_alt_group_combo_changed(self, combo):
		self.alternatives.dig(combo.get_active_text().lower(), 1)
		self.alt_theme_combo.remove_all()

		for name in self.alternatives.structure[1]['directories']:
			self.alt_theme_combo.append_text(name.capitalize())

		self.alt_theme_combo.set_active(0)

	def on_alt_theme_combo_changed(self, combo):
		text = combo.get_active_text()
		if text:
			self.alternatives.dig(text.lower(), 2)
			self.alt_icon_store.clear()

			for icon in self.alternatives.get_icons(2):
				pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon, self.view_icon_size, self.view_icon_size)
				self.alt_icon_store.append([pixbuf])

	def on_iconview_combo_changed(self, combo):
		text = combo.get_active_text()
		if text:
			self.iconview.dig(text.lower(), 1)
			self.iconview_store.clear()

			for icon in self.iconview.get_icons(1):
				pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon, self.view_icon_size, self.view_icon_size)
				self.iconview_store.append([pixbuf])

	def on_gradient_type_switched(self, combo):
		self.gradient.set_tag(combo.get_active_text())
		self.offset_write_to_config(['gradtype'])
		self.offset_read_from_config(['gradtype', 'direction'])

	def on_page_changed(self, nb, page, page_index):
		self.test_button.set_sensitive(page_index == 0 and not self.is_rtr_allowed)
		self.apply_button.set_sensitive(page_index in (0, 1))
		self.current_page_index = page_index

	def preview_update(self):
		"""Update icon preview"""

		if self.icongroups.current.is_double:
			icon1, icon2 = self.preview_file.name, self.icongroups.current.pair

			if self.icongroups.current.pairsw:
				icon1, icon2 = icon2, icon1

			pixbuf = self.icon_compose(icon1, icon2, self.preview_icon_size)
		else:
			pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(
				self.preview_file.name,
				self.preview_icon_size, self.preview_icon_size
			)

		self.preview_icon.set_from_pixbuf(pixbuf)

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

	def on_test_click(self, *args):
		if not self.is_preview_locked:
			self.offset_write_to_config()
			self.change_icon(self.preview_file.name)
			self.preview_update()

	def on_apply_click(self, widget, data=None):
		if self.current_page_index == 0:
			files = common.get_svg_list(*self.icongroups.current.realdirs)
			self.change_icon(*files)
		else:
			self.alternatives.send_icons(2, DIRS['main']['real'])

	def on_filter_settings_click(self, widget, data=None):
		self.filters.current.gui['window'].show_all()

	def on_icongroup_combo_changed(self, combo):

		self.offset_write_to_config()
		files = common.get_svg_list(*self.icongroups.current.testdirs)
		self.change_icon(*files)

		self.icongroups.switch(combo.get_active_text())
		self.icongroups.current.cache_preview(self.preview_file)

		if self.icongroups.current.is_custom:
			self.custom_icons_store.clear()
			for key, value in self.icongroups.current.state.items():
				self.custom_icons_store.append([key.capitalize(), value])

		self.custom_icon_tree_view.set_sensitive(self.icongroups.current.is_custom)

		self.offset_read_from_config()
		self.preview_update()

	def offset_read_from_config(self, keys=['direction', 'colors', 'filter', 'autooffset', 'gradtype']):
		self.is_preview_locked = True

		section = self.icongroups.current.name if self.icongroups.current.name in self.db else 'default'

		if 'colors' in keys:
			self.offset_list_store.clear()
			for color in self.db[section]['colors']:
				self.offset_list_store.append(color)

		if 'direction' in keys:
			self.direction_list_store.clear()
			for coord in self.db[section]['direction'][self.gradient.tag]:
				self.direction_list_store.append(coord)

		if 'autooffset' in keys:
			self.autooffset = self.db[section]['autooffset']
			self.offset_switch.set_active(not self.autooffset)

		if 'gradtype' in keys:
			self.gradient_combo.set_active(self.gradient.profile['index'])

		if 'filter' in keys:
			filter_ = self.db[section]['filter']
			self.filters_combo.set_active(self.filters.names.index(filter_) if filter_ in self.filters.names else 0)

		self.is_preview_locked = False
		self.change_icon(self.preview_file.name)
		self.preview_update()

	def offset_write_to_config(self, keys=['direction', 'colors', 'filter', 'autooffset', 'gradtype']):
		section = self.icongroups.current.name

		if section not in self.db:
			self.db[section] = deepcopy(self.db['default'])

		dump = self.db[section]

		if 'gradtype' in keys:
			dump['gradtype'] = self.gradient.tag
		if 'autooffset' in keys:
			dump['autooffset'] = self.autooffset
		if 'filter' in keys:
			dump['filter'] = self.filters_combo.get_active_text()
		if 'colors' in keys:
			dump['colors'] = [list(row) for row in self.offset_list_store]
		if 'direction' in keys:
			dump['direction'][self.gradient.tag] = [list(row) for row in self.direction_list_store]

		# if 'filtername' in dump: del dump['filtername']
		# if 'custom' in self.db: del self.db['custom']
		# self.db['default'] = deepcopy(self.db['Custom'])

		self.db[section] = dump

	def on_offset_structure_changed(self, model, *args):
		if self.autooffset:
			self.set_offset_auto()

		if len(model) > 0:
			self.offset_tree_view.set_cursor(len(model) - 1)
			self.offset_scale.set_value(model[len(model) - 1][2]) # fix this!!!

	def on_offset_selection_changed(self, selection):
		model, sel = selection.get_selected()

		if sel:
			self.offset_selected = sel
			color = model[sel][0]
			alpha = model[sel][1]
			self.color_selector_wr.set_hex_color(color, alpha)

			offset = model[sel][2]
			self.offset_scale.set_value(offset)

	def on_autooffset_toggled(self, switch, *args):
		is_active = switch.get_active()
		self.offset_scale.set_sensitive(is_active)
		self.autooffset = not is_active

		if self.autooffset:
			self.set_offset_auto()

		self.offset_scale.set_value(self.offset_list_store[self.offset_selected][2])
		self.real_time_render()

	def on_offset_value_changed(self, scale):
		offset = scale.get_value()
		self.offset_list_store.set_value(self.offset_selected, 2, int(offset))
		self.real_time_render()

	def on_color_change(self, *args):
		color, alpha = self.color_selector_wr.get_hex_color()
		self.offset_list_store.set_value(self.offset_selected, 0, color)
		self.offset_list_store.set_value(self.offset_selected, 1, alpha)
		self.real_time_render()

	def on_direction_edited(self, widget, path, text):
		self.direction_list_store[path][1] = int(text)
		self.real_time_render()

	def add_offset_line(self, *args):
		color, alpha = self.color_selector_wr.get_hex_color()
		self.offset_list_store.append([color, alpha, 100])

	def remove_offset_line(self, *args):
		if len(self.offset_list_store) > 1:
			self.offset_list_store.remove(self.offset_selected)

	def set_offset_auto(self):
		rownum = len(self.offset_list_store)
		if rownum > 1:
			step = 100 / (rownum - 1)
			for i, row in enumerate(self.offset_list_store):
				row[2] = i * step
		elif rownum == 1:
			self.offset_list_store[0][2] = 100

	def on_custom_icon_toggled(self, widget, path):
		self.custom_icons_store[path][1] = not self.custom_icons_store[path][1]
		name = self.custom_icons_store[path][0].lower()
		self.icongroups.current.switch_state(name)
		self.icongroups.current.cache_preview(self.preview_file)

		self.real_time_render()
		self.preview_update()

	def icon_compose(self, icon1, icon2, size):
		"""merge two icon in one"""
		pix = []
		pix.append(GdkPixbuf.Pixbuf.new_from_file_at_size(icon1, size, size))
		pix.append(GdkPixbuf.Pixbuf.new_from_file_at_size(icon2, size, size))

		GdkPixbuf.Pixbuf.composite(
			pix[1], pix[0],
			0, 0,
			size, size,
			size / 2, size / 2,
			0.5, 0.5,
			GdkPixbuf.InterpType.BILINEAR,
			255)

		return pix[0]

if __name__ == "__main__":
	main = Handler()
	main.fill_up_gui()

	Gtk.main()
