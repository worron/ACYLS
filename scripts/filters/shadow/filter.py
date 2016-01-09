import os
from common import FilterParameter, CustomFilterBase
from gi.repository import Gdk

class Filter(CustomFilterBase):

	def __init__(self):
		CustomFilterBase.__init__(self, os.path.dirname(__file__))
		self.name = "Drop Shadow"
		self.group = "Shadow"

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

		gui_elements = ("window", "alpha", "scale", "colorbutton", "blur", "dx", "dy")

		self.on_scale_changed = self.build_plain_handler('scale')
		self.on_dx_changed = self.build_plain_handler('dx')
		self.on_dy_changed = self.build_plain_handler('dy')
		self.on_alpha_changed = self.build_plain_handler('alpha')
		self.on_blur_changed = self.build_plain_handler('blur')
		self.on_colorbutton_set = self.build_color_handler('color')

		self.gui_load(gui_elements)
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
