import os
from common import FilterParameter, CustomFilterBase

class Filter(CustomFilterBase):

	def __init__(self):
		CustomFilterBase.__init__(self, os.path.dirname(__file__))
		self.name = "Stroke"

		gui_elements = ("window", "width", "scale")
		self.gui_load(gui_elements)

		# stroke_tag = self.dull['filter'].find(".//*[@id='support1']")
		stroke_tag = self.dull['visual'].find(".//*[@id='visible1']")
		self.param['width'] = FilterParameter(stroke_tag, 'style', r'width:(.+)', 'width:%.1f')

		scale_tag = self.dull['visual'].find(".//*[@id='visible1']")
		self.param['scale'] = FilterParameter(scale_tag, 'transform', r'scale\((.+)\) t', 'scale(%.2f) t')

		self.gui_setup()

	def gui_setup(self):
		self.gui['scale'].set_value(float(self.param['scale'].match()))
		self.gui['width'].set_value(float(self.param['width'].match()))

	def on_width_changed(self, scale):
		value = scale.get_value()
		self.param['width'].set_value(value)
		self.render.run(False)

	def on_scale_changed(self, scale):
		value = scale.get_value()
		self.param['scale'].set_value(value)
		self.render.run(False)
