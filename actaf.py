#!/usr/bin/env python
# -*- coding: utf8 -*-
# Taman.py
# This file is part of TaMan
#
# Copyright (C) 2009 - Carlos Flores
#
# TaMan is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# TaMan is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with TaMan; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, 
# Boston, MA  02110-1301  USA

import sys
import locale
try:
	import pygtk
	pygtk.require("2.0")
except:
	pass

try:
	import gtk
except:
	sys.exit(1)

from actaf import gui

if __name__ == "__main__":
	
	try:
		import psyco
		psyco.full()
	except ImportError:
		pass
	
	locale.setlocale(locale.LC_ALL, "")
	
	actaf = gui.MainWindow()
	gtk.main()

