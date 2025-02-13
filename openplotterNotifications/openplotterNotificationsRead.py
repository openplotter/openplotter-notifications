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
	def __init__(self, path, actions, notification,debug,currentLanguage,conf,platform,timestamp,repeated):
		threading.Thread.__init__(self)
		self.path = path
		self.actions = actions
		self.notification = notification
		self.debug = debug
		self.currentLanguage = currentLanguage
		self.conf = conf
		self.platform = platform
		self.timestamp = timestamp
		self.repeated = repeated

	def run(self):
		try:
			for a in self.actions:
				if a['enabled']:
					if self.repeated:
						if 'repeat' in a:
							if a['repeat'] != '1': continue
						else: continue
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
										data = data.replace('<|t|>',self.timestamp)
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
										result = re.findall(r'<\((.*?)\)>', data, re.DOTALL)
										for i in result:
											try:
												data2 = eval(i)
												data = data.replace('<('+i+')>',str(data2))
											except Exception as e:
												if self.debug: 
													print('Error processing expression in action data: '+str(e))
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
		visualList = {}
		soundList = {}
		actionsList2 = {}
		subprocess.call(['pkill','-f','openplotter-notifications-visual'])
		subprocess.call(['pkill','-f','openplotter-notifications-sound'])
		while True:
			if not ws:
				platform2 = platform.Platform()
				conf2 = conf.Conf()
				if conf2.get('GENERAL', 'debug') == 'yes': debug = True
				else: debug = False
				currentLanguage = conf2.get('GENERAL', 'lang')
				try: actionsList = eval(conf2.get('NOTIFICATIONS', 'actions'))
				except: actionsList = {}
				try: visualIgnore = eval(conf2.get('NOTIFICATIONS', 'visualIgnore'))
				except: visualIgnore = []
				try: soundIgnore = eval(conf2.get('NOTIFICATIONS', 'soundIgnore'))
				except: soundIgnore = []
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
					resp = requests.get(platform2.http+'localhost:'+platform2.skPort+'/signalk/v1/api/self', verify=False)
					uuid = resp.content
					uuid = uuid.decode("utf-8")
					uuid = uuid.replace('"', '')
					if "vessels.undefined" in uuid:
						if debug: 
							print('Undefined UUID or MMSI')
							sys.stdout.flush()
							subprocess.Popen(['set-notification','-v','notifications.server','alert', _('Undefined UUID or MMSI')])
				except Exception as e:
					ws = False
					if debug: 
						print('Error getting UUID or MMSI: '+str(e))
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
															if 'method' in value['value'] and 'state' in value['value'] and 'message' in value['value'] and 'timestamp' in update:
																if 'context' in data:
																	if uuid in data['context'] or data['context'] == 'vessels.self':
																		if 'visual' in value['value']['method']:
																			if not value['path'] in visualList or value['value']['state'] != visualList[value['path']]:
																				if value['value']['state'] not in visualIgnore:
																					subprocess.Popen(['openplotter-notifications-visual', value['path'], value['value']['state'], value['value']['message'], update['timestamp'], data['context']])
																				visualList[value['path']] = value['value']['state']
																		if 'sound' in value['value']['method']:
																			if not value['path'] in soundList or value['value']['state'] != soundList[value['path']]:
																				if value['value']['state'] not in soundIgnore:
																					subprocess.Popen(['openplotter-notifications-sound', value['path'], value['value']['state'], update['timestamp'], data['context']])
																				soundList[value['path']] = value['value']['state']
														else: 
															notification = {'state':'null','message':'','timestamp':'','method':[]}
															visualList[value['path']] = ''
															soundList[value['path']] = ''

														if 'context' in data:
															repeated = False
															actions = []
															context = data['context'].replace('vessels.','')
															if context in uuid or context == 'self':
																if 'self.'+value['path'] in actionsList:
																	contextPath = 'self.'+value['path']
																	actions.extend(actionsList[contextPath])
																	if not contextPath in actionsList2 or notification['state'] != actionsList2[contextPath]['state'] or notification['message'] != actionsList2[contextPath]['message']:
																		actionsList2[contextPath] = {'state':notification['state'],'message':notification['message']}
																	else: repeated = True
															if context+'.'+value['path'] in actionsList:
																contextPath = context+'.'+value['path']
																actions.extend(actionsList[contextPath])
																if not contextPath in actionsList2 or notification['state'] != actionsList2[contextPath]['state'] or notification['message'] != actionsList2[contextPath]['message']:
																	actionsList2[contextPath] = {'state':notification['state'],'message':notification['message']}
																else: repeated = True
															if actions:
																thread = processActions(value['path'],actions,notification,debug,currentLanguage,conf2,platform2,update['timestamp'],repeated)
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