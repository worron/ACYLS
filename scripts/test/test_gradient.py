# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import pytest
import basetest
import gradient
from lxml import etree


@pytest.mark.parametrize("gradiennt_tag, gradient_string", [
	('linearGradient', basetest.linear_gradient_string),
	('radialGradient', basetest.radial_gradient_string),
])
def test_gradient(gradiennt_tag, gradient_string):
	gr = gradient.Gradient(tag=gradiennt_tag)
	gr_build = etree.tostring(gr.build(basetest.data))
	assert gr_build == gradient_string.encode(encoding='UTF-8')
