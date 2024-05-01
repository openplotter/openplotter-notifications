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
from openplotterSettings import language

class Actions:
	def __init__(self,conf,currentLanguage):
		self.conf = conf
		currentdir = os.path.dirname(os.path.abspath(__file__))
		language.Language(currentdir,'openplotter-notifications',currentLanguage)
		if self.conf.get('GENERAL', 'debug') == 'yes': self.debug = True
		else: self.debug = False
		self.available = []
		self.available.append({'ID':'command','name':_('Run command'),"module": "openplotterNotifications",'data':True,'default':'echo "Hello World"','help':''})
		self.available.append({'ID':'reboot','name':_('Reboot'),"module": "openplotterNotifications",'data':False,'default':'','help':''})
		self.available.append({'ID':'shutdown','name':_('Shutdown'),"module": "openplotterNotifications",'data':False,'default':'','help':''})
		self.available.append({'ID':'notification','name':_('Set notification'),"module": "openplotterNotifications",'data':True,'default':'Signal_K_key=foo.bar\nnull=no\nstate=normal\nmessage=Hello World\nsound=no\nvisual=yes','help':_('Allowed values for state:')+' nominal, normal, alert, warn, alarm, emergency'})
		self.available.append({'ID':'sk','name':_('Set Signal K key'),"module": "openplotterNotifications",'data':True,'default':'Signal_K_key=foo.bar\nvalue=5','help':''})
		self.available.append({'ID':'sleep','name':_('Wait some seconds'),"module": "openplotterNotifications",'data':True,'default':'2','help':_('Enter the seconds to wait without quotes')})
		self.available.append({'ID':'check','name':_('Check notification again'),"module": "openplotterNotifications",'data':False,'default':'','help':''})
		if os.path.exists('/usr/share/applications/openplotter-brightness.desktop'):
			self.available.append({'ID':'backlight','name':_('Set backlight'),"module": "openplotterNotifications",'data':True,'default':'50','help':_('Enter a value between 0 and 100')})


	def run(self,action,data):
		try:
			if action == 'command': subprocess.Popen(data, shell=True)
			elif action == 'reboot': subprocess.Popen('reboot', shell=True)
			elif action == 'shutdown': subprocess.Popen('poweroff', shell=True)
			elif action == 'notification':
				Signal_K_key = ''
				null = False
				state = ''
				message = ''
				sound = False
				visual = False
				lines = data.split('\n')
				for i in lines:
					line = i.split('=')
					if line[0].strip() == 'Signal_K_key': Signal_K_key = line[1].strip()
					elif line[0].strip() == 'null':
						if line[1].strip()=="yes": null = True
					elif line[0].strip() == 'state': state = line[1].strip()
					elif line[0].strip() == 'message': message = line[1].strip()
					elif line[0].strip() == 'sound':
						if line[1].strip()=="yes": sound = True
					elif line[0].strip() == 'visual':
						if line[1].strip()=="yes": visual = True
				command = ['set-notification']
				if null: command.append('-n')
				if sound: command.append('-s')
				if visual: command.append('-v')
				command.append(Signal_K_key)
				command.append(state)
				command.append(message)
				process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
				out, err = process.communicate()
				if err:
					err = err.decode()
					err = err.replace('\n','')
					process2 = subprocess.Popen(['set-notification','-s','-v','notifications.openplotter.actions','alert', err], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
					out2, err2 = process2.communicate()
					if err2:
						if self.debug: print('Error setting notification: '+str(err2))
			elif action == 'sk':
				from openplotterSignalkInstaller import connections
				from openplotterSettings import platform
				from websocket import create_connection
				import ssl
				platform2 = platform.Platform()
				skConnections = connections.Connections('NOTIFICATIONS')
				token = skConnections.token
				uri = platform2.ws+'localhost:'+platform2.skPort+'/signalk/v1/stream?subscribe=none'
				if token:
					headers = {'Authorization': 'Bearer '+token}
					Signal_K_key = ''
					value =  ''
					lines = data.split('\n')
					for i in lines:
						line = i.split('=')
						if line[0].strip() == 'Signal_K_key': Signal_K_key = line[1].strip()
						elif line[0].strip() == 'value':
							value = line[1].strip()
							try: float(value)
							except: 
								if value != 'null': value = '"'+value+'"'
					if Signal_K_key and value:
						try:
							ws = create_connection(uri, header=headers, sslopt={"cert_reqs": ssl.CERT_NONE})
							ws.send('{"updates":[{"$source":"OpenPlotter.Actions.SendSignalKkey","values":[{"path":"'+Signal_K_key+'","value":'+value+'}]}]}\n')
							ws.close()
						except Exception as e:
							if self.debug: print('Error connecting to Signal K server: '+str(e))
				else:
					if self.debug: print('Error getting NOTIFICATIONS credentials')
			elif action == 'backlight':
				if os.path.exists('/usr/share/applications/openplotter-brightness.desktop'):
					from rpi_backlight import Backlight
					backlight = Backlight()
					with backlight.fade(duration=1):
						backlight.brightness = int(data)
		except Exception as e: 
			if self.debug: print('Error processing openplotter-notifications actions: '+str(e))
