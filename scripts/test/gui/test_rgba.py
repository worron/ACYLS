# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import pytest
from gi.repository import Gdk
import guisupport as acylgui


@pytest.mark.parametrize("hex_, hex_exp", [
	('#000000', '#000000'),
	('#7F7F7F', '#7F7F7F'),
	('#FFFFFF', '#FFFFFF'),
	('#007FFF', '#007FFF'),
	pytest.mark.xfail(('#000001', '#000000')),
	pytest.mark.xfail(('#FFFFFE', '#FFFFFF')),
])
def test_hex_from_rgba(hex_, hex_exp):
	rgba = Gdk.RGBA()
	rgba.parse(hex_)
	hex_acyl = acylgui.hex_from_rgba(rgba)
	assert hex_exp == hex_acyl
