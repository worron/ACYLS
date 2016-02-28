# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
# import pytest
import types


class Fake:
	def __init__(self, *methods):
		for name, method in methods:
			self.__dict__[name] = types.MethodType(method, self)


acyl_svg_string1_l = (
	'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="48" height="48">\n'
	'  <defs id="acyl-settings">\n'
	'    <linearGradient id="acyl-gradient" x1="0%" x2="0%" y1="0%" y2="100%">\n'
	'      <stop offset="0%" style="stop-color:#1AFF00;stop-opacity:1.000000"/>\n'
	'      <stop offset="50%" style="stop-color:#FFB300;stop-opacity:1.000000"/>\n'
	'      <stop offset="100%" style="stop-color:#FF4000;stop-opacity:1.000000"/>\n'
	'    </linearGradient>\n'
	'    <g id="acyl-filter">\n'
	'      <filter id="filter"/>\n'
	'    </g>\n'
	'    <g id="acyl-drawing">\n'
	'      <path d="M 2,5 2,43 46,24 z " id="path-main"/>\n'
	'    </g>\n'
	'  </defs>\n'
	'  <g id="acyl-visual">\n'
	'    <use id="visible1" style="fill:url(#acyl-gradient);filter:url(#filter)" xlink:href="#acyl-drawing"/>\n'
	'  </g>\n'
	'</svg>'
)

acyl_svg_string1_r = (
	'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="48" height="48">\n'
	'  <defs id="acyl-settings">\n'
	'    <radialGradient cx="50%" cy="50%" fx="50%" fy="50%" id="acyl-gradient" r="50%">\n'
	'      <stop offset="0%" style="stop-color:#1AFF00;stop-opacity:1.000000"/>\n'
	'      <stop offset="50%" style="stop-color:#FFB300;stop-opacity:1.000000"/>\n'
	'      <stop offset="100%" style="stop-color:#FF4000;stop-opacity:1.000000"/>\n'
	'    </radialGradient>\n'
	'    <g id="acyl-filter">\n'
	'      <filter id="filter"/>\n'
	'    </g>\n'
	'    <g id="acyl-drawing">\n'
	'      <path d="M 2,5 2,43 46,24 z " id="path-main"/>\n'
	'    </g>\n'
	'  </defs>\n'
	'  <g id="acyl-visual">\n'
	'    <use id="visible1" style="fill:url(#acyl-gradient);filter:url(#filter)" xlink:href="#acyl-drawing"/>\n'
	'  </g>\n'
	'</svg>'
)


data = {
	'gradtype': 'linearGradient',
	'filter': 'Disabled',
	'colors': [
		['#1AFF00', 1.0, 0, 'rgb(26,255,0)'],
		['#FFB300', 1.0, 50, 'rgb(255,179,0)'],
		['#FF4000', 1.0, 100, 'rgb(255,64,0)']
	],
	'autooffset': True,
	'direction': {
		'radialGradient': [['CenterX', 50], ['CenterY', 50], ['FocusX', 50], ['FocusY', 50], ['Radius', 50]],
		'linearGradient': [['StartX', 0], ['StartY', 0], ['EndX', 0], ['EndY', 100]]
	}
}


linear_gradient1_string = ''.join(acyl_svg_string1_l.split('\n')[2:7])
radial_gradient1_string = ''.join(acyl_svg_string1_r.split('\n')[2:7])
# filter1_string = ''.join(acyl_svg_string1_l.split('\n')[7:10])
# visual1_string = ''.join(acyl_svg_string1_l.split('\n')[14:17])
