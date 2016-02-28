# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import pytest
import basetest
import gradient
import base
from lxml import etree


@pytest.mark.parametrize("gradient_tag, gradient_string", [
	('linearGradient', basetest.linear_gradient1_string),
	('radialGradient', basetest.radial_gradient1_string),
])
def test_gradient(gradient_tag, gradient_string):
	reference_tag = etree.fromstring(gradient_string, base.parser)

	gradient_inst = gradient.Gradient(tag=gradient_tag)
	gradient_inst_xml = etree.tostring(gradient_inst.build(basetest.data))
	reference_xml = etree.tostring(reference_tag)
	assert gradient_inst_xml == reference_xml
