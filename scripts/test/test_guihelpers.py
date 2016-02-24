import os
import sys
import unittest

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../lib"))
from gi.repository import GdkPixbuf, Gdk
import guihelpers


test_svg = """
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="48" height="48">
<defs id="acyl-settings">
<linearGradient id="acyl-gradient" x1="0%" x2="0%" y1="0%" y2="100%">
<stop offset="100%" style="stop-color:#A0A0A0;stop-opacity:1.000000"/>
</linearGradient>
<g id="acyl-filter">
<filter id="filter"/>
</g>
<g id="acyl-drawing">
<path d="M 2,5 2,43 46,24 z " id="path-main"/>
</g>
</defs>
<g id="acyl-visual">
<use id="visible1" style="fill:url(#acyl-gradient);filter:url(#filter)" xlink:href="#acyl-drawing"/>
</g>
</svg>"""


class ActionHandlerTest(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		cls.runned = False

		def action():
			cls.runned = True

		cls.handler = guihelpers.ActionHandler(action)

	def setUp(self):
		ActionHandlerTest.runned = False

	def test_blocked_run(self):
		self.handler.set_state(False)
		self.handler.run()
		self.assertFalse(self.runned)

	def test_allowed_run(self):
		self.handler.set_state(True)
		self.handler.run()
		self.assertTrue(self.runned)

	def test_forced_run(self):
		self.handler.set_state(False)
		self.handler.run(forced=True)
		self.assertTrue(self.runned)


class PixbufCreatorTest(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		cls.rgba_color = Gdk.RGBA()
		cls.rgba_color.parse('#007FFF')
		cls.svg_bytes = test_svg.encode(encoding='UTF-8')

	def test_hex_from_rgba(self):
		hex = guihelpers.PixbufCreator.hex_from_rgba(self.rgba_color)
		self.assertEqual(hex, '#007FFF')

	def test_new_pixbuf_from_string(self):
		pixbuf = guihelpers.PixbufCreator.new_single_at_size(self.svg_bytes, size=120)
		self.assertIsInstance(pixbuf, GdkPixbuf.Pixbuf)

	def test_double_pixbuf_from_string(self):
		pixbuf = guihelpers.PixbufCreator.new_double_at_size(self.svg_bytes, self.svg_bytes, size=120)
		self.assertIsInstance(pixbuf, GdkPixbuf.Pixbuf)

	def test_double_pixbuf_from_string_size(self):
		pixbuf = guihelpers.PixbufCreator.new_double_at_size(self.svg_bytes, self.svg_bytes, size=120)
		self.assertTrue(pixbuf.get_width() == 120 and pixbuf.get_height() == 120)

if __name__ == '__main__':
	unittest.main()
