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

acyl_svg_string2_l = (
	'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="48" height="48">\n'
	'  <defs id="acyl-settings">\n'
	'    <linearGradient id="acyl-gradient" x1="0%" x2="0%" y1="0%" y2="100%">\n'
	'      <stop offset="0%" style="stop-color:#FF0000;stop-opacity:1.000000"/>\n'
	'      <stop offset="100%" style="stop-color:#0090FF;stop-opacity:1.000000"/>\n'
	'    </linearGradient>\n'
	'    <g id="acyl-filter">\n'
	'      <filter id="filter" x="-50%" y="-50%" width="200%" height="200%">\n'
	'        <feTurbulence id="feTurbulence1" result="result1" numOctaves="1" '
	'baseFrequency="0.20 0.06" type="turbulence"/>\n'
	'        <feGaussianBlur id="feGaussianBlur1" in="SourceGraphic" stdDeviation="2.0"/>\n'
	'        <feComposite id="feComposite1" operator="out" in2="result1"/>\n'
	'      </filter>\n'
	'    </g>\n'
	'    <g id="acyl-drawing">\n'
	'      <path d="M 2,5 2,43 46,24 z " id="path-main"/>\n'
	'    </g>\n'
	'  </defs>\n'
	'  <g id="acyl-visual">\n'
	'    <use id="visible1" transform="translate(24,24) scale(1.00) translate(-24,-24)" '
	'style="fill:url(#acyl-gradient);filter:url(#filter)" xlink:href="#acyl-drawing"/>\n'
	'  </g>\n'
	'</svg>'
)

acyl_svg_string2_r = (
	'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="48" height="48">\n'
	'  <defs id="acyl-settings">\n'
	'    <radialGradient cx="50%" cy="50%" fx="50%" fy="50%" id="acyl-gradient" r="50%">'
	'      <stop offset="0%" style="stop-color:#FF0000;stop-opacity:1.000000"/>'
	'      <stop offset="100%" style="stop-color:#0090FF;stop-opacity:1.000000"/>'
	'    </radialGradient>'
	'    <g id="acyl-filter">\n'
	'      <filter id="filter" x="-50%" y="-50%" width="200%" height="200%">\n'
	'        <feTurbulence id="feTurbulence1" result="result1" numOctaves="1" '
	'baseFrequency="0.20 0.06" type="turbulence"/>\n'
	'        <feGaussianBlur id="feGaussianBlur1" in="SourceGraphic" stdDeviation="2.0"/>\n'
	'        <feComposite id="feComposite1" operator="out" in2="result1"/>\n'
	'      </filter>\n'
	'    </g>\n'
	'    <g id="acyl-drawing">\n'
	'      <path d="M 2,5 2,43 46,24 z " id="path-main"/>\n'
	'    </g>\n'
	'  </defs>\n'
	'  <g id="acyl-visual">\n'
	'    <use id="visible1" transform="translate(24,24) scale(1.00) translate(-24,-24)" '
	'style="fill:url(#acyl-gradient);filter:url(#filter)" xlink:href="#acyl-drawing"/>\n'
	'  </g>\n'
	'</svg>'
)

data1 = {
	'gradtype': 'linearGradient',
	'filter': 'Disabled',
	'colors': [
		['#1AFF00', 1.0, 0, 'rgb(26,255,0)'],
		['#FFB300', 1.0, 50, 'rgb(255,179,0)'],
		['#FF4000', 1.0, 100, 'rgb(255,64,0)']
	],
	'autooffset': True,
	'radialGradient': [['CenterX', 50], ['CenterY', 50], ['FocusX', 50], ['FocusY', 50], ['Radius', 50]],
	'linearGradient': [['StartX', 0], ['StartY', 0], ['EndX', 0], ['EndY', 100]]
}


data2 = {
	'colors': [
		['#FF0000', 1.0, 0, 'rgb(255,0,0)'],
		['#0090FF', 1.0, 100, 'rgb(0,144,255)']
	],
	'filter': 'Flames',
	'radialGradient': [['CenterX', 50], ['CenterY', 50], ['FocusX', 50], ['FocusY', 50], ['Radius', 50]],
	'linearGradient': [['StartX', 0], ['StartY', 0], ['EndX', 0], ['EndY', 100]],
	'autooffset': True,
	'gradtype': 'linearGradient'
}
