#!/usr/bin/env python3

# This file is part of OpenPlotter.
# Copyright (C) 2022 by Sailoog <https://github.com/openplotter/openplotter-notifications>
#                     
# Openplotter is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# any later version.
# Openplotter is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Openplotter. If not, see <http://www.gnu.org/licenses/>.

import time, os, subprocess, sys
from openplotterSettings import language
from openplotterSignalkInstaller import connections

class Start():
	def __init__(self, conf, currentLanguage):
		self.conf = conf
		currentdir = os.path.dirname(os.path.abspath(__file__))
		language.Language(currentdir,'openplotter-notifications',currentLanguage)
		self.initialMessage = _('Starting Notifications...')

	def start(self): 
		green = '' 
		black = '' 
		red = '' 
		
		if self.conf.get('GENERAL', 'rescue') != 'yes':
			subprocess.call(['pkill', '-f', 'openplotter-notifications-read'])
			subprocess.Popen('openplotter-notifications-read')
			time.sleep(1)
			black = _('Notifications started')
		else: subprocess.call(['pkill', '-f', 'openplotter-notifications-read'])

		return {'green': green,'black': black,'red': red}

class Check():
	def __init__(self, conf, currentLanguage):
		self.conf = conf
		currentdir = os.path.dirname(os.path.abspath(__file__))
		language.Language(currentdir,'openplotter-notifications',currentLanguage)
		
		self.initialMessage = _('Checking Notifications...')

	def check(self): 
		green = '' 
		black = ''
		red = ''

		if self.conf.get('GENERAL', 'rescue') == 'yes':
			subprocess.call(['pkill', '-f', 'openplotter-notifications-read'])
			msg = _('Notifications is in rescue mode')
			if red: red += '\n   '+msg
			else: red = msg
		else:
			test = subprocess.check_output(['ps','aux']).decode(sys.stdin.encoding)
			if 'openplotter-notifications-read' in test: green = _('running')
			else:
				subprocess.Popen('openplotter-notifications-read')
				time.sleep(1)
				test = subprocess.check_output(['ps','aux']).decode(sys.stdin.encoding)
				if 'openplotter-notifications-read' in test: green = _('running')
				else:
					msg = _('not running')
					if red: red += '\n   '+msg
					else: red = msg

		#access
		skConnections = connections.Connections('NOTIFICATIONS')
		result = skConnections.checkConnection()
		if result[0] == 'pending' or result[0] == 'error' or result[0] == 'repeat' or result[0] == 'permissions':
			if not red: red = result[1]
			else: red+= '\n    '+result[1]
		if result[0] == 'approved' or result[0] == 'validated':
			msg = _('Access to Signal K server validated')
			if not black: black = msg
			else: black+= ' | '+msg

		return {'green': green,'black': black,'red': red}

