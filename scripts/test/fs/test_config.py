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
			# f.write(dir_ + file_)
			f.write("[test]\nvalue=%s" % dir_ + file_)

	def tmpdir_teardown():
		tdir.cleanup()

	request.addfinalizer(tmpdir_teardown)
	return os.path.join(tdir.name, "sys"), os.path.join(tdir.name, "user")


def test_filekeeper_copy(tmpdir):
	bakdir, curdir = tmpdir
	fs.ConfigReader(curdir, bakdir, "test1")
	assert os.path.isfile(os.path.join(curdir, "test1"))
