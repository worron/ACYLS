# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import pytest
import os
import imp
from filters import CustomFilterBase

filter_path = "filters"


@pytest.fixture(scope="module")
def connect_render():
	render = lambda *a: None
	render.run = lambda *a: None

	CustomFilterBase.connect_render(render)


def filter_files():
	flist = []
	for root, _, files in os.walk(filter_path):
		if 'filter.py' in files:
			flist.append(os.path.join(root, 'filter.py'))

	return flist


@pytest.mark.parametrize("file_", filter_files())
def test_filter_modules(file_, connect_render):
	try:
		module = imp.load_source('filter', file_)
		module.Filter()
	except Exception:
		pytest.fail("Cann't load %s" % file_)
