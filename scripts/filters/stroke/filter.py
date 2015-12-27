import os
from common import FilterParameter, CustomFilterBase
from gi.repository import Gdk

class Filter(CustomFilterBase):

	def __init__(self):
		CustomFilterBase.__init__(self, os.path.dirname(__file__))
		self.name = "Stroke"

		gui_elements = ("window", "width", "scale", "fill_colorbutton")
		self.gui_load(gui_elements)

		style_tag = self.dull['visual'].find(".//*[@id='visible1']")
		self.param['width'] = FilterParameter(style_tag, 'style', r'width:(.+)', 'width:%.1f')
		self.param['scale'] = FilterParameter(style_tag, 'transform', r'scale\((.+?)\) ', 'scale(%.2f) ')
		self.param['fill_color'] = FilterParameter(style_tag, 'style', r'rgb(\(.+?\));', 'rgb%s;')
		self.param['fill_alpha'] = FilterParameter(style_tag, 'style', r'fill-opacity:(.+?);', 'fill-opacity:%.2f;')

		self.gui_setup()

	def gui_setup(self):
		self.gui['scale'].set_value(float(self.param['scale'].match()))
		self.gui['width'].set_value(float(self.param['width'].match()))
		self.gui['fill_colorbutton'].set_alpha(float(self.param['fill_alpha'].match()) * 65535)

		rgb = [color / 255 * 65535 for color in eval(self.param['fill_color'].match())]
		self.gui['fill_colorbutton'].set_color(Gdk.Color(*rgb))

	def on_bg_colorbutton_set(self, widget, *args):
		# colors_str = "(%s)" % ",".join(["%d" % (color * 255) for color in widget.get_color().to_floats()])
		colors = [int(color * 255) for color in widget.get_color().to_floats()]
		self.param['fill_color'].set_value(str(tuple(colors)))
		alpha = widget.get_alpha() / 65535
		self.param['fill_alpha'].set_value(alpha)

		self.render.run(False, forced=True)

	def on_width_changed(self, scale):
		value = scale.get_value()
		self.param['width'].set_value(value)
		self.render.run(False)

	def on_scale_changed(self, scale):
		value = scale.get_value()
		self.param['scale'].set_value(value)
		self.render.run(False)
