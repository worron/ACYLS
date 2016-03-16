# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import pytest
import shelve
import basetest

dbfile = "data/default/store.acyl"
data_keywords = basetest.data1.keys()


@pytest.fixture(scope="module")
def base_dump():
	db = shelve.open(dbfile)
	dump = db['default']
	return dump


@pytest.mark.parametrize("section", data_keywords)
def test_database_structure(base_dump, section):
	assert section in base_dump.keys()
