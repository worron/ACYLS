# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

import os
from acyls.lib.filters import FilterParameter, CustomFilterBase


class Filter(CustomFilterBase):

	def __init__(self):
		CustomFilterBase.__init__(self, os.path.dirname(__file__))
		self.name = "Speckle"
		self.group = "Overlays"

		visible_tag = self.dull['visual'].find(".//*[@id='visible1']")
		turbulence_tag = self.dull['filter'].find(".//*[@id='feTurbulence1']")
		matrix_tag = self.dull['filter'].find(".//*[@id='feColorMatrix2']")

		self.param['scale'] = FilterParameter(visible_tag, 'transform', 'scale\((.+?)\) ', 'scale(%.2f) ')
		self.param['octaves'] = FilterParameter(turbulence_tag, 'numOctaves', '(.+)', '%.1f')
		self.param['sensation'] = FilterParameter(matrix_tag, 'values', '0 (\d+\.\d+) 0', '0 %.1f 0')
		self.param['frequency_x'] = FilterParameter(turbulence_tag, 'baseFrequency', '(.+?) ', '%.2f ')
		self.param['frequency_y'] = FilterParameter(turbulence_tag, 'baseFrequency', ' (.+)', ' %.2f')

		gui_elements = ["scale", "octaves", "frequency_x", "frequency_y", "sensation"]

		self.on_scale_changed = self.build_plain_handler('scale')
		self.on_sensation_changed = self.build_plain_handler('sensation')
		self.on_frequency_x_changed = self.build_plain_handler('frequency_x')
		self.on_frequency_y_changed = self.build_plain_handler('frequency_y')
		self.on_octaves_changed = self.build_plain_handler('octaves')

		self.gui_load(gui_elements)
		self.gui_setup()

		self.connect_scale_signal('scale', 'frequency_x', 'frequency_y', 'sensation', 'octaves')

	def gui_setup(self):
		self.gui_settler_plain('scale', 'frequency_x', 'frequency_y', 'sensation', 'octaves')
