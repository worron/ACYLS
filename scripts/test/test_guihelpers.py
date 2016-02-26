import os
import sys
import pytest
import tempfile

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


@pytest.fixture()
def handler():
	def action():
		action.runned = True

	action.runned = False
	return guihelpers.ActionHandler(action)


class TestActionHandler:

	def test_blocked_run(self, handler):
		handler.set_state(False)
		handler.run()
		assert not handler.action.runned

	def test_allowed_run(self, handler):
		handler.set_state(True)
		handler.run()
		assert handler.action.runned

	def test_forced_run(self, handler):
		handler.set_state(False)
		handler.run(forced=True)
		assert handler.action.runned


@pytest.fixture(params=['#000000', '#FFFFFF', '#7F7F7F', '#007FFF'])
def rgba(request):
	rgba_color = Gdk.RGBA()
	rgba_color.parse(request.param)
	rgba_color.test_hex_ = request.param
	return rgba_color


@pytest.fixture(scope="module")
def svg_bytes():
	return test_svg.encode(encoding='UTF-8')


@pytest.fixture()
def tmpsvg(request, svg_bytes):
	f = tempfile.NamedTemporaryFile(suffix='.svg')
	f.write(svg_bytes)
	f.seek(0)

	def tmpsvg_teardown():
		f.close()

	request.addfinalizer(tmpsvg_teardown)
	return f


class TestPixbufCreator:

	def test_hex_from_rgba(self, rgba):
		hex = guihelpers.PixbufCreator.hex_from_rgba(rgba)
		assert hex == rgba.test_hex_

	def test_new_pixbuf_from_file(self, tmpsvg):
		pixbuf = guihelpers.PixbufCreator.new_single_at_size(tmpsvg.name, size=120)
		assert isinstance(pixbuf, GdkPixbuf.Pixbuf)

	def test_new_pixbuf_from_string(self, svg_bytes):
		pixbuf = guihelpers.PixbufCreator.new_single_at_size(svg_bytes, size=120)
		assert isinstance(pixbuf, GdkPixbuf.Pixbuf)

	def test_double_pixbuf_from_string(self, svg_bytes):
		pixbuf = guihelpers.PixbufCreator.new_double_at_size(svg_bytes, svg_bytes, size=120)
		assert isinstance(pixbuf, GdkPixbuf.Pixbuf)

	@pytest.mark.parametrize("sz", [16, 48, 128])
	def test_double_pixbuf_from_string_size(self, svg_bytes, sz):
		pixbuf = guihelpers.PixbufCreator.new_double_at_size(svg_bytes, svg_bytes, size=sz)
		assert pixbuf.get_width() == sz and pixbuf.get_height() == sz
