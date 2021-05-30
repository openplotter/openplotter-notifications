#!/usr/bin/env python3

# This file is part of Openplotter.
# Copyright (C) 2021 by Sailoog <https://github.com/openplotter/openplotter-notifications>
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

	if state == 'normal':
		try: sound = eval(conf.get('NOTIFICATIONS', 'soundNormal'))
		except: sound = ['/usr/share/sounds/openplotter/Bleep.mp3', True]
	if state == 'alert':
		try: sound = eval(conf.get('NOTIFICATIONS', 'soundAlert'))
		except: sound = ['/usr/share/sounds/openplotter/Store_Door_Chime.mp3', True]
	if state == 'warn':
		try: sound = eval(conf.get('NOTIFICATIONS', 'soundWarn'))
		except: sound = ['/usr/share/sounds/openplotter/Ship_Bell.mp3', True]
	if state == 'alarm':
		try: sound = eval(conf.get('NOTIFICATIONS', 'soundAlarm'))
		except: sound = ['/usr/share/sounds/openplotter/House_Fire_Alarm.mp3', False]
	if state == 'emergency':
		try: sound = eval(conf.get('NOTIFICATIONS', 'soundEmergency'))
		except: sound = ['/usr/share/sounds/openplotter/Tornado_Siren_II.mp3', False]

	while True:
		subprocess.call(['cvlc', '--play-and-exit', sound[0]])
		if sound[1]:
			try:
				path2 = path.replace('.','/')
				resp = requests.get(platform2.http+'localhost:'+platform2.skPort+'/signalk/v1/api/vessels/self/'+path2, verify=False)
				data = ujson.loads(resp.content)
			except: data = {}
			if 'value' in data:
				if not data['value']: break
				elif 'state' in data['value']:
					if data['value']['state'] != state: break
					else:
						if 'timestamp' in data['value']:
							if data['value']['timestamp'] != timestamp: break
				else: break
			else: break
		time.sleep(1)

if __name__ == '__main__':
	main()
