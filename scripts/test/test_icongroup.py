# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import pytest
import icongroup
import tempfile
import os


@pytest.fixture(scope="module")
def simple_dir(request):
	tdir = tempfile.TemporaryDirectory()
	icondir = dict(root=tdir.name)

	for dirname in ("real", "prev", "prev_back", "prev_empty"):
		newdir = os.path.join(tdir.name, dirname)
		os.mkdir(newdir)
		icondir[dirname] = newdir

	for dir_, txt in [("real", "real_preview_icon"), ("prev", "standart_preview_icon")]:
		for i in range(1, 3):
			with open(os.path.join(tdir.name, dir_, "%d.svg" % i), "w") as f:
				f.write(txt)

	with open(os.path.join(tdir.name, "prev_back", "icon.svg"), "w") as f:
		f.write("backup_preview_icon")

	def tmpdir_teardown():
		tdir.cleanup()

	request.addfinalizer(tmpdir_teardown)
	return icondir


@pytest.fixture(scope="module")
def custom_dir(request):
	tdir = tempfile.TemporaryDirectory()
	icondir = dict(root=tdir.name)

	for dirname in ("real", "prev", "prev_back", "prev_empty"):
		newdir = os.path.join(tdir.name, dirname)
		os.mkdir(newdir)
		icondir[dirname] = newdir

	for custom_dir in ("real", "prev"):
		for subdir in ("first", "second"):
			newdir = os.path.join(tdir.name, custom_dir, subdir)
			os.mkdir(newdir)
			with open(os.path.join(newdir, "icon.svg"), "w") as f:
				f.write("%s_%s_svg_icon" % (subdir, custom_dir))

	with open(os.path.join(tdir.name, "prev_back", "icon.svg"), "w") as f:
		f.write("backup_preview_icon")

	def tmpdir_teardown():
		tdir.cleanup()

	request.addfinalizer(tmpdir_teardown)
	return icondir


@pytest.mark.parametrize("prev_dir, preview_txt", [
	('prev', b"standart_preview_icon"),
	('prev_empty', b"backup_preview_icon"),
])
def test_simple_group_prev(simple_dir, prev_dir, preview_txt):
	group = icongroup.BasicIconGroup("simple", simple_dir['prev_back'], [simple_dir[prev_dir]], [simple_dir['real']])
	assert group.preview == preview_txt


@pytest.mark.parametrize("icon", ["1.svg", "2.svg"])
def test_simple_group_get_real(simple_dir, icon):
	group = icongroup.BasicIconGroup("simple", simple_dir['prev_back'], [simple_dir['prev']], [simple_dir['real']])
	real_icons = group.get_real()
	assert os.path.join(simple_dir['root'], "real", icon) in real_icons


@pytest.mark.parametrize("icon", ["1.svg", "2.svg"])
def test_simple_group_get_test(simple_dir, icon):
	group = icongroup.BasicIconGroup("simple", simple_dir['prev_back'], [simple_dir['prev']], [simple_dir['real']])
	prev_icons = group.get_test()
	assert os.path.join(simple_dir['root'], "prev", icon) in prev_icons


@pytest.mark.parametrize("subgroup, preview_txt", [
	("first", b"first_prev_svg_icon"),
	("second", b"second_prev_svg_icon"),
])
def test_custom_group_switch(custom_dir, subgroup, preview_txt):
	group = icongroup.CustomIconGroup("simple", custom_dir['prev_back'], custom_dir['prev'], custom_dir['real'])
	group.switch_state(subgroup)
	real_icons = group.get_real()
	assert group.preview == preview_txt and os.path.join(custom_dir['root'], "real", subgroup, "icon.svg") in real_icons
