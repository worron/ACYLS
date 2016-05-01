# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import pytest
import os
import imp

filter_path = "scripts/filters"


def filter_files():
	flist = []
	for root, _, files in os.walk(filter_path):
		if 'filter.py' in files:
			flist.append(os.path.join(root, 'filter.py'))

	return flist


@pytest.mark.parametrize("file_", filter_files())
def test_filter_modules(file_):
	try:
		module = imp.load_source('filter', file_)
		module.Filter()
	except Exception:
		pytest.fail("Cann't load %s" % file_)
