import os
from common import FilterParameter, CustomFilterBase
from gi.repository import Gdk

class Filter(CustomFilterBase):

	def __init__(self):
		CustomFilterBase.__init__(self, os.path.dirname(__file__))
		self.name = "Stroke"

		gui_elements = ("window", "width", "scale", "fill_colorbutton")
		self.gui_load(gui_elements)

		visible_tag = self.dull['visual'].find(".//*[@id='visible1']")
		self.param['width'] = FilterParameter(visible_tag, 'style', 'width:(.+)', 'width:%.1f')
		self.param['scale'] = FilterParameter(visible_tag, 'transform', 'scale\((.+?)\) ', 'scale(%.2f) ')
		self.param['fill_color'] = FilterParameter(visible_tag, 'style', '(rgb\(.+?\));', '%s;')
		self.param['fill_alpha'] = FilterParameter(visible_tag, 'style', 'fill-opacity:(.+?);', 'fill-opacity:%.2f;')

		self.gui_setup()

	def gui_setup(self):
		self.gui['scale'].set_value(float(self.param['scale'].match()))
		self.gui['width'].set_value(float(self.param['width'].match()))

		rgba = Gdk.RGBA()
		rgba.parse(self.param['fill_color'].match())
		rgba.alpha = float(self.param['fill_alpha'].match())
		self.gui['fill_colorbutton'].set_rgba(rgba)

	def on_bg_colorbutton_set(self, widget, *args):
		rgba = widget.get_rgba()
		self.param['fill_alpha'].set_value(rgba.alpha)
		rgba.alpha = 1 # dirty trick
		self.param['fill_color'].set_value(rgba.to_string())

		self.render.run(False, forced=True)

	def on_width_changed(self, scale):
		value = scale.get_value()
		self.param['width'].set_value(value)
		self.render.run(False)

	def on_scale_changed(self, scale):
		value = scale.get_value()
		self.param['scale'].set_value(value)
		self.render.run(False)
