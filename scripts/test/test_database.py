# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import os
import pytest
import basetest
import data
import shelve
import tempfile


@pytest.fixture()
def tmpdb(request):
	f = tempfile.NamedTemporaryFile()
	d = shelve.open(f.name, 'n')
	d['first'] = basetest.data1
	d['default'] = basetest.data1
	d['second'] = basetest.data2

	def tmpdb_teardown():
		f.close()

	request.addfinalizer(tmpdb_teardown)
	return f.name


@pytest.fixture()
def tmpdb_reverse(request):
	f = tempfile.NamedTemporaryFile()
	d = shelve.open(f.name, 'n')
	d['first'] = basetest.data2
	d['default'] = basetest.data2
	d['second'] = basetest.data1

	def tmpdb_teardown():
		f.close()

	request.addfinalizer(tmpdb_teardown)
	return f.name


@pytest.fixture()
def tmpfile(request):
	tdir = tempfile.TemporaryDirectory()

	def tmpdir_teardown():
		tdir.cleanup()

	request.addfinalizer(tmpdir_teardown)
	return os.path.join(tdir.name, "data.db")


@pytest.mark.parametrize("section, orig_data", [
	('first', basetest.data1),
	('second', basetest.data2),
])
def test_base_creation(tmpfile, section, orig_data):
	db = data.DataStore(tmpfile, ddate={'first': basetest.data1, 'second': basetest.data2}, dsection='first')
	d = db.db[section]
	assert d == orig_data


@pytest.mark.parametrize("section, orig_data", [
	('first', basetest.data1),
	pytest.mark.xfail(('first', basetest.data2)),
	('default', basetest.data1),
	('second', basetest.data2),
])
def test_base_init(tmpdb, section, orig_data):
	db = data.DataStore(tmpdb)
	d = db.get_dump(section)
	assert d == orig_data


def test_base_reset(tmpdb):
	db = data.DataStore(tmpdb)
	db.reset('second')
	d = db.get_dump('second')
	assert d == basetest.data1


@pytest.mark.parametrize("section, orig_data", [('first', basetest.data1), ('second', basetest.data2)])
@pytest.mark.parametrize("key", basetest.data1.keys())
def test_base_keys(tmpdb, key, section, orig_data):
	db = data.DataStore(tmpdb)
	key_object = db.get_key(section, key)
	assert key_object == orig_data[key]


def test_base_clear(tmpdb):
	db = data.DataStore(tmpdb)
	db.clear(['first'])
	d = db.get_dump('second')
	assert d == basetest.data1


@pytest.mark.parametrize("section, orig_data", [('first', basetest.data2), ('second', basetest.data1)])
def test_base_load(tmpdb, tmpdb_reverse, section, orig_data):
	db = data.DataStore(tmpdb)
	db.load_from_file(tmpdb_reverse)
	d = db.get_dump(section)
	assert d == orig_data


@pytest.mark.parametrize("section, orig_data", [('first', basetest.data1), ('second', basetest.data2)])
def test_base_save(tmpdb, tmpdb_reverse, section, orig_data):
	db = data.DataStore(tmpdb)
	db.save_to_file(tmpdb_reverse)

	with shelve.open(tmpdb_reverse) as saved_db:
		d = saved_db[section]

	assert d == orig_data
