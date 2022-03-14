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

import sys, ssl, time, ujson, subprocess
from openplotterSettings import conf
from openplotterSettings import platform
from websocket import create_connection

def main():
	ws = False
	while True:
		if not ws:
			platform2 = platform.Platform()
			conf2 = conf.Conf()
			if conf2.get('GENERAL', 'debug') == 'yes': debug = True
			else: debug = False
			token = conf2.get('NOTIFICATIONS', 'token')
			uri = platform2.ws+'localhost:'+platform2.skPort+'/signalk/v1/stream?subscribe=none'
			if token:
				headers = {'Authorization': 'Bearer '+token}
				try:
					ws = create_connection(uri, header=headers, sslopt={"cert_reqs": ssl.CERT_NONE})
				except Exception as e:
					ws = False
					if debug: print('Error connecting to Signal K server: '+str(e))
		if ws:
			try: ws.send('{"context": "vessels.self","subscribe":[{"path":"notifications.*"}]}\n')
			except: 
				if ws: ws.close()
				ws = False
			else:
				while True:
					time.sleep(0.1)
					try:
						try: 
							if ws: result = ws.recv()
							else: break
						except: 
							if ws: ws.close()
							ws = False
							break
						else:
							data = ujson.loads(result)
							if 'updates' in data:
								for update in data['updates']:
									if 'values' in update:
										for value in update['values']:
											if 'notifications.' in value['path']: 
												if value['value']:
													if 'method' in value['value']:
														if 'visual' in value['value']['method']: 
															subprocess.Popen(['openplotter-notifications-visual', value['path'], value['value']['state'], value['value']['message'], value['value']['timestamp']])	
														if 'sound' in value['value']['method']:
															subprocess.Popen(['openplotter-notifications-sound', value['path'], value['value']['state'], value['value']['timestamp']])				
					except Exception as e: 
						if debug: print('Error reading Signal K notifications: '+str(e))
		time.sleep(5)

if __name__ == '__main__':
	main()