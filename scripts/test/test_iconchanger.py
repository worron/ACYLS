# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import pytest
import basetest
import iconchanger
import base
from lxml import etree


@pytest.mark.parametrize("input_svg, reference_svg", [
	(basetest.acyl_svg_string1_l, basetest.acyl_svg_string1_l),
	(basetest.acyl_svg_string1_r, basetest.acyl_svg_string1_l),
	(basetest.acyl_svg_string1_l, basetest.acyl_svg_string1_r),
])
def test_changer_text(input_svg, reference_svg):
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

	svg_changed_bytes = iconchanger.rebuild_text(input_svg, fake_gradient, fake_filter, None)
	reference_svg_bytes = etree.tostring(etree.fromstring(reference_svg, base.parser))
	assert svg_changed_bytes == reference_svg_bytes
