# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import pytest
import basetest
import iconchanger
import base
from lxml import etree
import tempfile


@pytest.fixture(params=[basetest.acyl_svg_string1_l, basetest.acyl_svg_string2_l])
def tmpsvg(request):
	f = tempfile.NamedTemporaryFile(suffix='.svg')
	f.write(request.param.encode(encoding='UTF-8'))
	f.seek(0)

	def tmpsvg_teardown():
		f.close()

	request.addfinalizer(tmpsvg_teardown)
	return f


def build_fake_objects(reference_svg):
	reference_root = etree.fromstring(reference_svg, base.parser)
	reference_filter_tag = reference_root.find(".//*[@id='acyl-filter']")
	reference_visual_tag = reference_root.find(".//*[@id='acyl-visual']")
	reference_gradient_tag = reference_root.find(".//*[@id='acyl-gradient']")
	reference_dull = dict(filter=reference_filter_tag, visual=reference_visual_tag)

	def fake_gradient_build(self, _):
		return reference_gradient_tag

	def fake_filter_get(self):
		return reference_dull

	fake_gradient = basetest.Fake(('build', fake_gradient_build))
	fake_filter = basetest.Fake(('get', fake_filter_get))

	return fake_gradient, fake_filter


@pytest.mark.parametrize("input_svg, reference_svg", [
	(basetest.acyl_svg_string1_l, basetest.acyl_svg_string1_r),
	(basetest.acyl_svg_string1_l, basetest.acyl_svg_string2_l),
	(basetest.acyl_svg_string1_l, basetest.acyl_svg_string2_r),
	(basetest.acyl_svg_string1_r, basetest.acyl_svg_string1_l),
	(basetest.acyl_svg_string1_r, basetest.acyl_svg_string2_l),
	(basetest.acyl_svg_string1_r, basetest.acyl_svg_string2_r),
	(basetest.acyl_svg_string2_l, basetest.acyl_svg_string1_r),
	(basetest.acyl_svg_string2_r, basetest.acyl_svg_string1_l),
])
def test_changer_text(input_svg, reference_svg):
	fake_gradient, fake_filter = build_fake_objects(reference_svg)

	changed_svg_bytes = iconchanger.rebuild_text(input_svg, fake_gradient, fake_filter, None)
	reference_svg_bytes = etree.tostring(etree.fromstring(reference_svg, base.parser))
	assert changed_svg_bytes == reference_svg_bytes


@pytest.mark.parametrize("reference_svg", [
	basetest.acyl_svg_string1_l,
	basetest.acyl_svg_string1_r,
	basetest.acyl_svg_string2_l,
	basetest.acyl_svg_string2_r,
])
def test_changer_file(reference_svg, tmpsvg):
	fake_gradient, fake_filter = build_fake_objects(reference_svg)
	reference_svg_bytes = etree.tostring(etree.fromstring(reference_svg, base.parser), pretty_print=True)

	iconchanger.rebuild(tmpsvg.name, gradient=fake_gradient, gfilter=fake_filter, data=None)
	assert tmpsvg.read() == reference_svg_bytes
