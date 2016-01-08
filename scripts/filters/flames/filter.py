import os
from common import FilterParameter, CustomFilterBase

class Filter(CustomFilterBase):

	def __init__(self):
		CustomFilterBase.__init__(self, os.path.dirname(__file__))
		self.name = "Flames"
		self.group = "Old"

		gui_elements = ("window", "scale", "octaves", "frequency_x", "frequency_y", "blur")
		self.gui_load(gui_elements)

		visible_tag = self.dull['visual'].find(".//*[@id='visible1']")
		turbulence_tag = self.dull['filter'].find(".//*[@id='feTurbulence1']")
		blur_tag = self.dull['filter'].find(".//*[@id='feGaussianBlur1']")

		self.param['scale'] = FilterParameter(visible_tag, 'transform', 'scale\((.+?)\) ', 'scale(%.2f) ')
		self.param['octaves'] = FilterParameter(turbulence_tag, 'numOctaves', '(.+)', '%d')
		self.param['blur'] = FilterParameter(blur_tag, 'stdDeviation', '(.+)', '%.1f')
		self.param['frequency_x'] = FilterParameter(turbulence_tag, 'baseFrequency', '(.+?) ', '%.2f ')
		self.param['frequency_y'] = FilterParameter(turbulence_tag, 'baseFrequency', ' (.+)', ' %.2f')

		self.gui_setup()

	def gui_setup(self):
		self.gui['scale'].set_value(float(self.param['scale'].match()))
		self.gui['frequency_x'].set_value(float(self.param['frequency_x'].match()))
		self.gui['frequency_y'].set_value(float(self.param['frequency_y'].match()))
		self.gui['blur'].set_value(float(self.param['blur'].match()))
		self.gui['octaves'].set_value(int(self.param['octaves'].match()))

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

	def on_blur_changed(self, spin):
		value = spin.get_value()
		self.param['blur'].set_value(value)
		self.render.run(False)

	def on_octaves_changed(self, scale):
		value = int(scale.get_value())
		self.param['octaves'].set_value(value)
		self.render.run(False)
