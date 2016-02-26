# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import pytest


acyl_svg_string = """
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="48" height="48">
<defs id="acyl-settings">
<linearGradient id="acyl-gradient" x1="0%" x2="0%" y1="0%" y2="100%">
<stop offset="100%" style="stop-color:#A0A0A0;stop-opacity:1.000000"/>
</linearGradient>
<g id="acyl-filter">
<filter id="filter"/>
</g>
<g id="acyl-drawing">
<path d="M 2,5 2,43 46,24 z " id="path-main"/>
</g>
</defs>
<g id="acyl-visual">
<use id="visible1" style="fill:url(#acyl-gradient);filter:url(#filter)" xlink:href="#acyl-drawing"/>
</g>
</svg>"""


@pytest.fixture(scope="module")
def svg_bytes():
	return acyl_svg_string.encode(encoding='UTF-8')
