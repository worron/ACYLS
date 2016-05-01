# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import pytest
import tempfile

from gi.repository import GdkPixbuf
import guisupport as acylgui
import basetest


@pytest.fixture()
def tmpsvg(request, svg_bytes):
	f = tempfile.NamedTemporaryFile(suffix='.svg')
	f.write(svg_bytes)
	f.seek(0)

	def tmpsvg_teardown():
		f.close()

	request.addfinalizer(tmpsvg_teardown)
	return f


@pytest.fixture(scope="module", params=[basetest.acyl_svg_string1_l, basetest.acyl_svg_string2_l])
def svg_bytes(request):
	return request.param.encode(encoding='UTF-8')


def test_new_pixbuf_from_file(tmpsvg):
	pixbuf = acylgui.PixbufCreator.new_single_at_size(tmpsvg.name, size=120)
	assert isinstance(pixbuf, GdkPixbuf.Pixbuf)


def test_new_pixbuf_from_string(svg_bytes):
	pixbuf = acylgui.PixbufCreator.new_single_at_size(svg_bytes, size=120)
	assert isinstance(pixbuf, GdkPixbuf.Pixbuf)


def test_double_pixbuf_from_string(svg_bytes):
	pixbuf = acylgui.PixbufCreator.new_double_at_size(svg_bytes, svg_bytes, size=120)
	assert isinstance(pixbuf, GdkPixbuf.Pixbuf)


@pytest.mark.parametrize("sz", [16, 48, 128])
def test_double_pixbuf_from_string_size(svg_bytes, sz):
	pixbuf = acylgui.PixbufCreator.new_double_at_size(svg_bytes, svg_bytes, size=sz)
	assert pixbuf.get_width() == sz and pixbuf.get_height() == sz
