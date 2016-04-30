# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import os
import sys


sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../lib"))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

import scripts
sys.modules['acyls'] = scripts

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
