import os
from common import FilterParameter, CustomFilterBase
from gi.repository import Gdk

class Filter(CustomFilterBase):

	def __init__(self):
		CustomFilterBase.__init__(self, os.path.dirname(__file__))
		self.name = "Scale"

		gui_elements = ("window", "scale")
		self.gui_load(gui_elements)

		visible_tag = self.dull['visual'].find(".//*[@id='visible1']")
		self.param['scale'] = FilterParameter(visible_tag, 'transform', 'scale\((.+?)\) ', 'scale(%.2f) ')

		self.gui_setup()

	def gui_setup(self):
		self.gui['scale'].set_value(float(self.param['scale'].match()))

	def on_scale_changed(self, scale):
		value = scale.get_value()
		self.param['scale'].set_value(value)
		self.render.run(False)
