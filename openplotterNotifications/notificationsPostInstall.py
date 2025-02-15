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

import os, subprocess
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

	print(_('Installing/Updating signalk-zones plugin...'))
	try:
		if platform2.skDir:
			subprocess.call(['npm', 'i', '--verbose', '@signalk/zones'], cwd = platform2.skDir)
		else: print(_('Failed. Please, install Signal K server.'))
		print(_('DONE'))
	except Exception as e: print(_('FAILED: ')+str(e))

	print(_('Creating services...'))
	try:
		if not os.path.exists(conf2.home+'/.config'): os.mkdir(conf2.home+'/.config')
		if not os.path.exists(conf2.home+'/.config/systemd'): os.mkdir(conf2.home+'/.config/systemd')
		if not os.path.exists(conf2.home+'/.config/systemd/user'): os.mkdir(conf2.home+'/.config/systemd/user')
		fo = open(conf2.home+'/.config/systemd/user/openplotter-notifications-read.service', "w")
		fo.write( '[Service]\nEnvironment=OPrescue=0\nEnvironmentFile=-/boot/firmware/config.txt\nExecStart=openplotter-notifications-read $OPrescue\nRestart=always\nRestartSec=3')
		fo.close()
		subprocess.call(['systemctl', '--user','daemon-reload'])
		subprocess.call(['systemctl', '--user','restart', 'openplotter-notifications-read'])
		print(_('DONE'))
	except Exception as e: print(_('FAILED: ')+str(e))

	print(_('Setting version...'))
	try:
		conf2.set('APPS', 'notifications', version)
		print(_('DONE'))
	except Exception as e: print(_('FAILED: ')+str(e))

if __name__ == '__main__':
	main()