# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import pytest
import configparser
import os

from icongroup import BasicIconGroup, CustomIconGroup

configfile = "scripts/data/default/config.ini"
config = configparser.ConfigParser()
config.read(configfile)


def grouplist():
	gl = [section for section in config.sections() if section.startswith('IconGroup')]
	return gl


def custom_grouplist():
	gl = [s for s in config.sections() if s.startswith('IconGroup') and config.getboolean(s, 'custom')]
	return gl


@pytest.mark.parametrize("section", grouplist())
def test_icongroup_config(section):
	try:
		is_custom = config.getboolean(section, 'custom')

		args = ("name", "pairdir", "emptydir", "testbase", "realbase")
		kargs = {k: config.get(section, k) for k in args if config.has_option(section, k)}

		args_l = ("testdirs", "realdirs")
		kargs_l = {k: config.get(section, k).split(";") for k in args_l if config.has_option(section, k)}

		args_b = ("pairsw",)
		kargs_b = {k: config.getboolean(section, k) for k in args_b if config.has_option(section, k)}

		for d in (kargs_l, kargs_b):
			kargs.update(d)

		IconGroupClass = CustomIconGroup if is_custom else BasicIconGroup
		IconGroupClass(**kargs)
	except Exception as e:
		print(e)
		pytest.fail("Cann't load %s" % section)


@pytest.mark.parametrize("section", custom_grouplist())
def test_custom_icongroup_directory_tree(section):
	dirs = {k: config.get(section, k) for k in ("testbase", "realbase") if config.has_option(section, k)}
	real_dir_list = next(os.walk(dirs['realbase']))[1]
	preview_dir_list = next(os.walk(dirs['testbase']))[1]
	is_ok = True
	for dir_ in preview_dir_list:
		is_ok = is_ok and dir_ in real_dir_list
	assert is_ok
