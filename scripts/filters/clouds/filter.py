import os
from common import FilterParameter, CustomFilterBase
from gi.repository import Gdk

class Filter(CustomFilterBase):

	def __init__(self):
		CustomFilterBase.__init__(self, os.path.dirname(__file__))
		self.name = "Clouds"
		self.group = "Overlays"

		gui_elements = ("window", "scale", "octaves", "frequency_x", "frequency_y", "colorbutton")
		self.gui_load(gui_elements)

		visible_tag = self.dull['visual'].find(".//*[@id='visible1']")
		turbulence_tag = self.dull['filter'].find(".//*[@id='feTurbulence1']")
		flood_tag = self.dull['filter'].find(".//*[@id='feFlood1']")

		self.param['scale'] = FilterParameter(visible_tag, 'transform', 'scale\((.+?)\) ', 'scale(%.2f) ')
		self.param['octaves'] = FilterParameter(turbulence_tag, 'numOctaves', '(.+)', '%d')
		self.param['frequency_x'] = FilterParameter(turbulence_tag, 'baseFrequency', '(.+?) ', '%.2f ')
		self.param['frequency_y'] = FilterParameter(turbulence_tag, 'baseFrequency', ' (.+)', ' %.2f')
		self.param['color'] = FilterParameter(flood_tag, 'flood-color', '(.+)', '%s')
		self.param['alpha'] = FilterParameter(flood_tag, 'flood-opacity', '(.+)', '%.2f')

		self.gui_setup()

	def gui_setup(self):
		self.gui['scale'].set_value(float(self.param['scale'].match()))
		self.gui['frequency_x'].set_value(float(self.param['frequency_x'].match()))
		self.gui['frequency_y'].set_value(float(self.param['frequency_y'].match()))
		self.gui['octaves'].set_value(int(self.param['octaves'].match()))

		rgba = Gdk.RGBA()
		rgba.parse(self.param['color'].match())
		rgba.alpha = float(self.param['alpha'].match())
		self.gui['colorbutton'].set_rgba(rgba)

	def on_scale_changed(self, scale):
		value = scale.get_value()
		self.param['scale'].set_value(value)
		self.render.run(False)

	def on_colorbutton_set(self, widget, *args):
		rgba = widget.get_rgba()
		self.param['alpha'].set_value(rgba.alpha)
		rgba.alpha = 1 # dirty trick
		self.param['color'].set_value(rgba.to_string())

		self.render.run(False, forced=True)

	def on_frequency_x_changed(self, spin):
		value = spin.get_value()
		self.param['frequency_x'].set_value(value)
		self.render.run(False)

	def on_frequency_y_changed(self, spin):
		value = spin.get_value()
		self.param['frequency_y'].set_value(value)
		self.render.run(False)

	def on_octaves_changed(self, scale):
		value = int(scale.get_value())
		self.param['octaves'].set_value(value)
		self.render.run(False)
