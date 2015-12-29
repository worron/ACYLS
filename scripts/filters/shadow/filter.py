import os
from common import FilterParameter, CustomFilterBase
from gi.repository import Gdk

class Filter(CustomFilterBase):

	def __init__(self):
		CustomFilterBase.__init__(self, os.path.dirname(__file__))
		self.name = "Shadow"

		gui_elements = ("window", "alpha", "scale", "colorbutton", "blur", "dx", "dy")
		self.gui_load(gui_elements)

		visible_tag = self.dull['visual'].find(".//*[@id='visible1']")
		flood_tag = self.dull['filter'].find(".//*[@id='feFlood1']")
		blur_tag = self.dull['filter'].find(".//*[@id='feGaussianBlur1']")
		offset_tag = self.dull['filter'].find(".//*[@id='feOffset1']")

		self.param['alpha'] = FilterParameter(flood_tag, 'flood-opacity', '(.+)', '%.2f')
		self.param['dx'] = FilterParameter(offset_tag, 'dx', '(.+)', '%.1f')
		self.param['dy'] = FilterParameter(offset_tag, 'dy', '(.+)', '%.1f')
		self.param['blur'] = FilterParameter(blur_tag, 'stdDeviation', '(.+)', '%.1f')
		self.param['scale'] = FilterParameter(visible_tag, 'transform', 'scale\((.+?)\) ', 'scale(%.2f) ')
		self.param['color'] = FilterParameter(flood_tag, 'flood-color', '(.+)', '%s')

		self.gui_setup()

	def gui_setup(self):
		self.gui['scale'].set_value(float(self.param['scale'].match()))
		self.gui['alpha'].set_value(float(self.param['alpha'].match()))
		self.gui['blur'].set_value(float(self.param['blur'].match()))
		self.gui['dx'].set_value(float(self.param['dx'].match()))
		self.gui['dy'].set_value(float(self.param['dy'].match()))

		rgba = Gdk.RGBA()
		rgba.parse(self.param['color'].match())
		self.gui['colorbutton'].set_rgba(rgba)

	def on_colorbutton_set(self, widget, *args):
		rgba = widget.get_rgba()
		self.param['color'].set_value(rgba.to_string())
		self.render.run(False, forced=True)

	def on_blur_changed(self, scale):
		value = scale.get_value()
		self.param['blur'].set_value(value)
		self.render.run(False)

	def on_alpha_changed(self, scale):
		value = scale.get_value()
		self.param['alpha'].set_value(value)
		self.render.run(False)

	def on_scale_changed(self, scale):
		value = scale.get_value()
		self.param['scale'].set_value(value)
		self.render.run(False)

	def on_dx_changed(self, spin):
		value = spin.get_value()
		self.param['dx'].set_value(value)
		self.render.run(False)

	def on_dy_changed(self, spin):
		value = spin.get_value()
		self.param['dy'].set_value(value)
		self.render.run(False)
