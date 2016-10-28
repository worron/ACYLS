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
		fullname = os.path.join(tdir.name, dir_, file_)
		with open(fullname, "a+") as f:
			f.write("[test]\nfile=%s\n" % (dir_ + file_))
			if dir_ == "sys":
				f.write("backup=backup_value\npath=backup_path\n")
			else:
				f.write("path=/broken_path\n")

	def tmpdir_teardown():
		tdir.cleanup()

	request.addfinalizer(tmpdir_teardown)
	return os.path.join(tdir.name, "sys"), os.path.join(tdir.name, "user")


def test_config_file_copy(tmpdir):
	bakdir, curdir = tmpdir
	fs.ConfigReader(curdir, bakdir, "test1")
	assert os.path.isfile(os.path.join(curdir, "test1"))


@pytest.mark.parametrize("option, result", [
	("file", "usertest2"),
	("backup", "backup_value"),
])
def test_config_value_get(option, result, tmpdir):
	bakdir, curdir = tmpdir
	config = fs.ConfigReader(curdir, bakdir, "test2")
	assert config.get("test", option) == result


def test_config_directory_validation(tmpdir):
	bakdir, curdir = tmpdir
	config = fs.ConfigReader(curdir, bakdir, "test2")
	assert config.getdir("test", "path") == "backup_path"
