import os
from common import FilterParameter, CustomFilterBase

class Filter(CustomFilterBase):

	def __init__(self):
		CustomFilterBase.__init__(self, os.path.dirname(__file__))
		self.name = "Tartan"
		self.group = "Overlays"

		gui_elements = ("window", "scale", "octaves_x", "octaves_y", "frequency_x", "frequency_y")
		self.gui_load(gui_elements)

		visible_tag = self.dull['visual'].find(".//*[@id='visible1']")
		turbulence1_tag = self.dull['filter'].find(".//*[@id='feTurbulence1']")
		turbulence2_tag = self.dull['filter'].find(".//*[@id='feTurbulence2']")
		matrix_tag = self.dull['filter'].find(".//*[@id='feColorMatrix2']")

		self.param['scale'] = FilterParameter(visible_tag, 'transform', 'scale\((.+?)\) ', 'scale(%.2f) ')
		self.param['octaves_x'] = FilterParameter(turbulence2_tag, 'numOctaves', '(.+)', '%d')
		self.param['octaves_y'] = FilterParameter(turbulence1_tag, 'numOctaves', '(.+)', '%d')
		self.param['frequency_x'] = FilterParameter(turbulence2_tag, 'baseFrequency', '(.+?) ', '%.2f ')
		self.param['frequency_y'] = FilterParameter(turbulence1_tag, 'baseFrequency', ' (.+)', ' %.2f')
		self.gui_setup()

	def gui_setup(self):
		self.gui['scale'].set_value(float(self.param['scale'].match()))
		self.gui['frequency_x'].set_value(float(self.param['frequency_x'].match()))
		self.gui['frequency_y'].set_value(float(self.param['frequency_y'].match()))
		self.gui['octaves_x'].set_value(int(self.param['octaves_x'].match()))
		self.gui['octaves_y'].set_value(int(self.param['octaves_y'].match()))

	def on_scale_changed(self, scale):
		value = scale.get_value()
		self.param['scale'].set_value(value)
		self.render.run(False)

	def on_frequency_x_changed(self, spin):
		value = spin.get_value()
		self.param['frequency_x'].set_value(value)
		self.render.run(False)

	def on_frequency_y_changed(self, spin):
		value = spin.get_value()
		self.param['frequency_y'].set_value(value)
		self.render.run(False)

	def on_octaves_x_changed(self, scale):
		value = int(scale.get_value())
		self.param['octaves_x'].set_value(value)
		self.render.run(False)

	def on_octaves_y_changed(self, scale):
		value = int(scale.get_value())
		self.param['octaves_y'].set_value(value)
		self.render.run(False)
