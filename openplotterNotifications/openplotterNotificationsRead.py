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

import sys, ssl, time, ujson, subprocess, threading, importlib, requests, re
from openplotterSettings import conf
from openplotterSettings import platform
from websocket import create_connection
from openplotterSignalkInstaller import connections

class processActions(threading.Thread):
	def __init__(self, path, actions, notification,debug,currentLanguage,conf,platform):
		threading.Thread.__init__(self)
		self.path = path
		self.actions = actions
		self.notification = notification
		self.debug = debug
		self.currentLanguage = currentLanguage
		self.conf = conf
		self.platform = platform

	def run(self):
		try:
			for a in self.actions:
				if a['enabled']:
					if not a['state'] or self.notification['state'] == a['state']:
						if not a['message'] or self.notification['message'] == a['message']:
							module = a['module']
							ID = a['ID']
							data = a['data']
							if module == 'openplotterNotifications' and a['ID'] == 'sleep': time.sleep(float(data))
							elif module == 'openplotterNotifications' and a['ID'] == 'check':
								try:
									path = self.path.replace('.','/')
									resp = requests.get(self.platform.http+'localhost:'+self.platform.skPort+'/signalk/v1/api/vessels/'+path, verify=False)
									data = ujson.loads(resp.content)
								except: data = {}
								if self.notification['state'] == 'null' and 'value' in data and not data['value']: pass
								elif 'value' in data and 'state' in data['value'] and data['value']['state'] == self.notification['state'] and 'message' in data['value'] and data['value']['message'] == self.notification['message']: pass
								else: return
							else:
								actions = False
								try:
									actions = importlib.import_module(module+'.actions')
									if actions: 
										target = actions.Actions(self.conf,self.currentLanguage)
										data = data.replace('<|s|>',self.notification['state'])
										data = data.replace('<|m|>',self.notification['message'])
										data = data.replace('<|t|>',self.notification['timestamp'])
										result = re.findall(r'<\|(.*?)\|>', data, re.DOTALL)
										for i in result:
											items = i.split('||')
											try:
												path = items[1].replace('.','/')
												resp = requests.get(self.platform.http+'localhost:'+self.platform.skPort+'/signalk/v1/api/vessels/'+items[0]+'/'+path, verify=False)
												data2 = ujson.loads(resp.content)
												data = data.replace('<|'+i+'|>',str(data2['value']))
											except Exception as e:
												if self.debug: 
													print('Error processing keys in action data: '+str(e))
													sys.stdout.flush()
										target.run(ID,data)
								except Exception as e:
									if self.debug: 
										print('Error processing action data: '+str(e))
										sys.stdout.flush()
		except Exception as e:
			if self.debug: 
				print('Error processing actions: '+str(e))
				sys.stdout.flush()

def main():
	if sys.argv[1] != '1':
		ws = False
		while True:
			if not ws:
				platform2 = platform.Platform()
				conf2 = conf.Conf()
				if conf2.get('GENERAL', 'debug') == 'yes': debug = True
				else: debug = False
				if conf2.get('GENERAL', 'rescue') == 'yes': sys.exit('Notifications in rescue mode')
				currentLanguage = conf2.get('GENERAL', 'lang')
				try: actionsList = eval(conf2.get('NOTIFICATIONS', 'actions'))
				except: actionsList = {}
				skConnections = connections.Connections('NOTIFICATIONS')
				token = skConnections.token
				try:
					uri = platform2.ws+'localhost:'+platform2.skPort+'/signalk/v1/stream?subscribe=none'
					if token:
						headers = {'Authorization': 'Bearer '+token}
						ws = create_connection(uri, header=headers, sslopt={"cert_reqs": ssl.CERT_NONE})
				except Exception as e:
					ws = False
					if debug: 
						print('Error connecting to Signal K server: '+str(e))
						sys.stdout.flush()
				try:
					resp = requests.get(platform2.http+'localhost:'+platform2.skPort+'/signalk/v1/api/vessels/self/uuid', verify=False)
					uuid = resp.content
					uuid = uuid.decode("utf-8")
					uuid = uuid.replace('"', '') 
				except Exception as e:
					ws = False
					if debug: 
						print('Error getting Signal K UUID: '+str(e))
						sys.stdout.flush()
			if ws:
				try: ws.send('{"context": "vessels.*","subscribe":[{"path":"notifications.*"}]}\n')
				except: 
					if ws: ws.close()
					ws = False
				else:
					while True:
						try:
							try: 
								if ws: result = ws.recv()
								else: break
							except: 
								if ws: ws.close()
								ws = False
								break
							else:
								try:
									data = ujson.loads(result)
									if 'updates' in data:
										for update in data['updates']:
											if 'values' in update:
												for value in update['values']:
													if 'notifications.' in value['path']:
														if value['value']:
															notification = value['value']
															if 'method' in value['value']:
																if 'context' in data:
																	if data['context'] == 'vessels.'+uuid or data['context'] == 'vessels.self':
																		if 'visual' in value['value']['method']: 
																			subprocess.Popen(['openplotter-notifications-visual', value['path'], value['value']['state'], value['value']['message'], value['value']['timestamp']])	
																		if 'sound' in value['value']['method']:
																			subprocess.Popen(['openplotter-notifications-sound', value['path'], value['value']['state'], value['value']['timestamp']])
														else: notification = {'state':'null','message':'','timestamp':'','method':[]}
														if 'context' in data:
															actions = ''
															context = data['context'].replace('vessels.','')
															if context+'.'+value['path'] in actionsList: actions = actionsList[context+'.'+value['path']]
															else:
																if context == uuid:
																	if 'self.'+value['path'] in actionsList: actions = actionsList['self.'+value['path']]
															if actions:
																thread = processActions(value['path'],actions,notification,debug,currentLanguage,conf2,platform2)
																thread.start()
								except Exception as e: 
									if debug: 
										print('Error processing notification: '+str(e))
										sys.stdout.flush()
						except Exception as e: 
							if debug: 
								print('Error reading Signal K notifications: '+str(e))
								sys.stdout.flush()
			time.sleep(5)

if __name__ == '__main__':
	main()