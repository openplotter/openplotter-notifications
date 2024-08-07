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

import sys, time, ujson, requests, subprocess
from openplotterSettings import conf
from openplotterSettings import platform
	
def main():
	platform2 = platform.Platform()
	conf2 = conf.Conf()

	path = sys.argv[1]
	state = sys.argv[2]
	timestamp = sys.argv[3]
	context = sys.argv[4]

	if state == 'nominal':
		try: sound = eval(conf2.get('NOTIFICATIONS', 'soundNominal'))
		except: sound = ['/usr/share/sounds/openplotter/bip.mp3', True]
	elif state == 'normal':
		try: sound = eval(conf2.get('NOTIFICATIONS', 'soundNormal'))
		except: sound = ['/usr/share/sounds/openplotter/Bleep.mp3', True]
	elif state == 'alert':
		try: sound = eval(conf2.get('NOTIFICATIONS', 'soundAlert'))
		except: sound = ['/usr/share/sounds/openplotter/Store_Door_Chime.mp3', True]
	elif state == 'warn':
		try: sound = eval(conf2.get('NOTIFICATIONS', 'soundWarn'))
		except: sound = ['/usr/share/sounds/openplotter/Ship_Bell.mp3', True]
	elif state == 'alarm':
		try: sound = eval(conf2.get('NOTIFICATIONS', 'soundAlarm'))
		except: sound = ['/usr/share/sounds/openplotter/pup-alert.mp3', False]
	elif state == 'emergency':
		try: sound = eval(conf2.get('NOTIFICATIONS', 'soundEmergency'))
		except: sound = ['/usr/share/sounds/openplotter/nuclear-alarm.ogg', False]

	while True:
		subprocess.call(['cvlc', '--play-and-exit', sound[0]])
		if sound[1]:
			try:
				path2 = path.replace('.','/')
				context2 = context.replace('.','/')
				resp = requests.get(platform2.http+'localhost:'+platform2.skPort+'/signalk/v1/api/'+context2+'/'+path2, verify=False)
				data = ujson.loads(resp.content)
			except: data = {}
			if 'value' in data:
				if not data['value']: break
				elif 'state' in data['value']:
					if data['value']['state'] != state: break
				else: break
			else: break
		time.sleep(3)

if __name__ == '__main__':
	main()
