# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import pytest
import basetest
import gradient
import base
from lxml import etree


@pytest.mark.parametrize("gradient_tag, input_svg, data", [
	('linearGradient', basetest.acyl_svg_string1_l, basetest.data1),
	('radialGradient', basetest.acyl_svg_string1_r, basetest.data1),
	pytest.mark.xfail(('radialGradient', basetest.acyl_svg_string1_l, basetest.data1)),
	pytest.mark.xfail(('linearGradient', basetest.acyl_svg_string1_l, basetest.data2)),
	('linearGradient', basetest.acyl_svg_string2_l, basetest.data2),
	('radialGradient', basetest.acyl_svg_string2_r, basetest.data2),
	pytest.mark.xfail(('radialGradient', basetest.acyl_svg_string2_l, basetest.data2)),
	pytest.mark.xfail(('linearGradient', basetest.acyl_svg_string2_l, basetest.data1)),
])
def test_gradient(gradient_tag, input_svg, data):
	input_root = etree.fromstring(input_svg, base.parser)
	input_gradient_tag = input_root.find(".//*[@id='acyl-gradient']")

	gradient_inst = gradient.Gradient(tag=gradient_tag)
	input_gradient_tag.getparent().replace(input_gradient_tag, gradient_inst.build(data))

	changed_svg_bytes = etree.tostring(input_root)
	reference_svg_bytes = etree.tostring(etree.fromstring(input_svg, base.parser))
	assert changed_svg_bytes == reference_svg_bytes
