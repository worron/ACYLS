# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import pytest
import fssupport as fs
import tempfile
import os


@pytest.fixture(scope="module")
def tmpdir(request):
	tdir = tempfile.TemporaryDirectory()

	for i in range(1, 3):
		groupdir = os.path.join(tdir.name, "group%d" % i)
		os.mkdir(groupdir)
		for j in range(1, 4):
			theme_index = (i - 1) * 3 + j
			themedir = os.path.join(groupdir, "theme%d" % theme_index)
			os.mkdir(themedir)
			for k in range(1, 4):
				with open(os.path.join(themedir, "icon%d-%d.svg" % (theme_index, k)), "w") as f:
					f.write("new")
			with open(os.path.join(themedir, "trash.png"), "w") as f:
					f.write("")

	def tmpdir_teardown():
		tdir.cleanup()

	request.addfinalizer(tmpdir_teardown)
	return tdir.name


@pytest.fixture()
def desttmpdir(request):
	tdir = tempfile.TemporaryDirectory()
	with open(os.path.join(tdir.name, "icon1-2.svg"), "w") as f:
		f.write("old")

	def tmpdir_teardown():
		tdir.cleanup()

	request.addfinalizer(tmpdir_teardown)
	return tdir.name


@pytest.mark.parametrize("group", ["group1", "group2"])
def test_prospector_root(group, tmpdir):
	prospector = fs.Prospector(tmpdir)
	assert group in prospector.structure[0]['directories']


@pytest.mark.parametrize("group, theme", [
	("group1", "theme1"),
	("group1", "theme3"),
	pytest.mark.xfail(("group1", "theme4")),
	("group2", "theme4"),
	("group2", "theme6"),
	pytest.mark.xfail(("group2", "theme1")),
])
def test_prospector_level(group, theme, tmpdir):
	prospector = fs.Prospector(tmpdir)
	prospector.dig(group, 1)
	assert theme in prospector.structure[1]['directories']


@pytest.mark.parametrize("group, theme, icon", [
	("group1", "theme1", "icon1-1.svg"),
	("group1", "theme2", "icon2-3.svg"),
	("group2", "theme4", "icon4-3.svg"),
	("group2", "theme6", "icon6-2.svg"),
	pytest.mark.xfail(("group1", "theme1", "icon4-1.svg")),
	pytest.mark.xfail(("group1", "theme1", "trash.png")),
])
def test_prospector_get_svg(group, theme, icon, tmpdir):
	prospector = fs.Prospector(tmpdir)
	prospector.dig(group, 1)
	prospector.dig(theme, 2)
	found_icons = prospector.get_icons(2)
	assert os.path.join(prospector.structure[2]['root'], icon) in found_icons


@pytest.mark.parametrize("icon", ["icon1-1.svg", "icon1-2.svg"])
def test_prospector_copy_svg(tmpdir, desttmpdir, icon):
	prospector = fs.Prospector(tmpdir)
	prospector.dig("group1", 1)
	prospector.dig("theme1", 2)
	prospector.send_icons(2, desttmpdir)

	with open(os.path.join(desttmpdir, icon), 'r') as f:
		data = f.read()

	assert data == "new"
