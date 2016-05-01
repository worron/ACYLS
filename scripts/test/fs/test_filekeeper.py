# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import pytest
import fssupport as fs
import tempfile
import os


@pytest.fixture()
def tmpdir(request):
	tdir = tempfile.TemporaryDirectory()

	for d in ("user", "sys"):
		os.mkdir(os.path.join(tdir.name, d))

	for dir_, file_ in (("sys", "test1"), ("sys", "test2"), ("user", "test2")):
		with open(os.path.join(tdir.name, dir_, file_), "w") as f:
			f.write(dir_ + file_)

	def tmpdir_teardown():
		tdir.cleanup()

	request.addfinalizer(tmpdir_teardown)
	return os.path.join(tdir.name, "sys"), os.path.join(tdir.name, "user")


def test_filekeeper_copy(tmpdir):
	bakdir, curdir = tmpdir
	keeper = fs.FileKeeper(bakdir, curdir)
	assert os.path.isfile(keeper.get("test1"))


def test_filekeeper_save_user_data(tmpdir):
	bakdir, curdir = tmpdir
	keeper = fs.FileKeeper(bakdir, curdir)
	with open(keeper.get("test2"), "r") as f:
		keep = f.read()
	with open(os.path.join(bakdir, "test2"), "r") as f:
		back = f.read()
	assert keep != back
