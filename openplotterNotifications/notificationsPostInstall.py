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

import os, sys, subprocess
from openplotterSettings import conf
from openplotterSettings import language
from openplotterSettings import platform
from .version import version

def main():
	conf2 = conf.Conf()
	currentdir = os.path.dirname(os.path.abspath(__file__))
	currentLanguage = conf2.get('GENERAL', 'lang')
	package = 'openplotter-notifications' 
	language.Language(currentdir, package, currentLanguage)
	platform2 = platform.Platform()

	print(_('Installing python packages...'))
	try:
		subprocess.call(['pip3', 'install', 'websocket-client', '-U'])
		print(_('DONE'))
	except Exception as e: print(_('FAILED: ')+str(e))

	print(_('Installing/Updating signalk-threshold-notifier plugin...'))
	try:
		if platform2.skDir:
			subprocess.call(['npm', 'i', '--verbose', 'signalk-threshold-notifier'], cwd = platform2.skDir)
			subprocess.call(['chown', '-R', conf2.user, platform2.skDir])
			subprocess.call(['systemctl', 'stop', 'signalk.service'])
			subprocess.call(['systemctl', 'stop', 'signalk.socket'])
			subprocess.call(['systemctl', 'start', 'signalk.socket'])
			subprocess.call(['systemctl', 'start', 'signalk.service'])
		else: print(_('Failed. Please, install Signal K server.'))
		print(_('DONE'))
	except Exception as e: print(_('FAILED: ')+str(e))

	print(_('Checking access to Signal K server...'))
	try:
		from openplotterSignalkInstaller import connections
		skConnections = connections.Connections('NOTIFICATIONS')
		result = skConnections.checkConnection()
		if result[1]: print(result[1])
		else: print(_('DONE'))
	except Exception as e: print(_('FAILED: ')+str(e))

	print(_('Adding openplotter-notifications-read service...'))
	try:
		autostartFolder = conf2.home+'/.config/autostart'
		if not os.path.exists(autostartFolder): os.mkdir(autostartFolder)
		subprocess.call(['cp', '-f', currentdir+'/data/openplotter-notifications-read.desktop', autostartFolder])
		subprocess.call(['pkill', '-f', 'openplotter-notifications-read'])
		subprocess.Popen('openplotter-notifications-read')
		print(_('DONE'))
	except Exception as e: print(_('FAILED: ')+str(e))
	
	print(_('Setting version...'))
	try:
		conf2.set('APPS', 'notifications', version)
		print(_('DONE'))
	except Exception as e: print(_('FAILED: ')+str(e))

if __name__ == '__main__':
	main()