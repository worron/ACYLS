#!/usr/bin/env python3
# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

import os
import sys

# Check requirements
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

if sys.version_info < (3, 4):
	sys.stdout.write("Requires Python 3.x\n")
	sys.exit(1)

# User modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "libacyl"))

# from mainwindow import MainWindow
from libacyl.mainwindow import MainWindow

# Run application
if __name__ == "__main__":
	os.chdir(os.path.dirname(os.path.abspath(__file__)))
	MainWindow()
	Gtk.main()
