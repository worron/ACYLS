import os
from common import SimpleFilterBase

class Filter(SimpleFilterBase):

	def __init__(self, *args):
		SimpleFilterBase.__init__(self, os.path.dirname(__file__))
		self.name = "Canvas"
		self.group = "Bumps"
