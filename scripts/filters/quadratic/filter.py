import os
from common import FilterParameter, CustomFilterBase

class Filter(CustomFilterBase):

	def __init__(self):
		CustomFilterBase.__init__(self, os.path.dirname(__file__))
		self.name = "Quadratic"

		visible_tag = self.dull['visual'].find(".//*[@id='visible1']")
		support1_tag = self.dull['filter'].find(".//*[@id='support1']")
		support2_tag = self.dull['filter'].find(".//*[@id='support2']")

		self.param['scale_icon'] = FilterParameter(support1_tag, 'transform', 'scale\((.+?)\) ', 'scale(%.2f) ')
		self.param['scale'] = FilterParameter(visible_tag, 'transform', 'scale\((.+?)\) ', 'scale(%.2f) ')
		self.param['rx'] = FilterParameter(visible_tag, 'rx', '(.+)', '%.1f')
		self.param['ry'] = FilterParameter(visible_tag, 'ry', '(.+)', '%.1f')
		self.param['color'] = FilterParameter(support2_tag, 'style', '(rgb\(.+?\));', '%s;')
		self.param['alpha'] = FilterParameter(support2_tag, 'style', 'fill-opacity:(.+)', 'fill-opacity:%.2f')

		gui_elements = ("window", "scale", "scale_icon", "radius", "colorbutton")

		self.on_scale_changed = self.build_plain_handler('scale')
		self.on_scale_icon_changed = self.build_plain_handler('scale_icon')
		self.on_radius_changed = self.build_plain_handler('rx', 'ry')
		self.on_colorbutton_set = self.build_color_handler('color', 'alpha')

		self.gui_load(gui_elements)
		self.gui_setup()

	def gui_setup(self):
		self.gui['radius'].set_value(float(self.param['rx'].match()))
		self.gui_settler_plain('scale', 'scale_icon')
		self.gui_settler_color('colorbutton', 'color', 'alpha')
