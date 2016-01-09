import os
from common import FilterParameter, CustomFilterBase
from gi.repository import Gdk

class Filter(CustomFilterBase):

	def __init__(self):
		CustomFilterBase.__init__(self, os.path.dirname(__file__))
		self.name = "Stroke"

		visible_tag = self.dull['visual'].find(".//*[@id='visible1']")
		self.param['width'] = FilterParameter(visible_tag, 'style', 'width:(.+)', 'width:%.1f')
		self.param['scale'] = FilterParameter(visible_tag, 'transform', 'scale\((.+?)\) ', 'scale(%.2f) ')
		self.param['color'] = FilterParameter(visible_tag, 'style', '(rgb\(.+?\));', '%s;')
		self.param['alpha'] = FilterParameter(visible_tag, 'style', 'fill-opacity:(.+?);', 'fill-opacity:%.2f;')

		gui_elements = ("window", "width", "scale", "colorbutton")

		self.on_scale_changed = self.build_plain_handler('scale')
		self.on_width_changed = self.build_plain_handler('width')
		self.on_colorbutton_set = self.build_color_handler('color', 'alpha')

		self.gui_load(gui_elements)
		self.gui_setup()

	def gui_setup(self):
		self.gui['scale'].set_value(float(self.param['scale'].match()))
		self.gui['width'].set_value(float(self.param['width'].match()))

		rgba = Gdk.RGBA()
		rgba.parse(self.param['color'].match())
		rgba.alpha = float(self.param['alpha'].match())
		self.gui['colorbutton'].set_rgba(rgba)
