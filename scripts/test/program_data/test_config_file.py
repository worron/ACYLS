# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import pytest
import configparser


configfile = "scripts/data/default/config.ini"
options = {
	'PreviewSize': ['single', 'group'],
	'Settings': ['autorender'],
	'Directories': ['real', 'alternatives'],
	'Editor': ['preview'],
	'IconGroup1': [],
}
sections_list = options.keys()


@pytest.fixture(scope="module")
def config():
	conf = configparser.ConfigParser()
	conf.read(configfile)
	return conf


@pytest.mark.parametrize("section", sections_list)
def test_config_options(config, section):
	is_ok = config.has_section(section)
	for option in options[section]:
		is_ok = is_ok and config.has_option(section, option)
	assert is_ok


def test_icongroup_order(config):
	icongroup_numbers = [int(section[9:]) for section in config.sections() if section.startswith('IconGroup')]
	assert sorted(icongroup_numbers) == list(range(1, max(icongroup_numbers) + 1))
