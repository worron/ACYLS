# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import pytest
import fssupport as fs
import os
import test_icondig
tmpdir = test_icondig.tmpdir


@pytest.mark.parametrize("icon", [
	("icon1-1.svg"),
	("icon2-3.svg"),
	("icon4-3.svg"),
	("icon6-2.svg"),
	pytest.mark.xfail(("trash.png")),
])
def test_get_svg_all(tmpdir, icon):
	svg_list = fs.get_svg_all(tmpdir)
	basenames = [os.path.basename(fullname) for fullname in svg_list]
	assert icon in basenames


def test_get_svg_first(tmpdir):
	svg_icon = fs.get_svg_first(tmpdir)
	assert os.path.isfile(svg_icon) and svg_icon.endswith('.svg')
