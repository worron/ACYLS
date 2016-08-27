# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import pytest
import base


@pytest.fixture()
def testpack():
	tpack = base.ItemPack()
	tpack.pack = {'seventh': "7", 'second': "2", 'fifth': "5"}
	tpack.build_names(lambda x: len(x))
	return tpack


@pytest.mark.parametrize("name", [
	"seventh", "second", "fifth", pytest.mark.xfail("first"),
])
def test_pack_names(testpack, name):
	assert name in testpack.names


@pytest.mark.parametrize("name_to_set, expected", [
	("second", "2"),
	("seventh", "7"),
	("first", "5"),
])
def test_pack_current(testpack, name_to_set, expected):
	testpack.switch(name_to_set)
	assert testpack.current == expected


def test_pack_current_init(testpack):
	assert testpack.current == "5"
