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

import sys, ssl, re
from openplotterSettings import platform
from websocket import create_connection
from openplotterSignalkInstaller import connections

def checkConn():
	skConnections = connections.Connections('NOTIFICATIONS')
	result = skConnections.checkConnection()
	if result[0] == 'error': sys.exit(str(result))

def send(sk,value):
	platform2 = platform.Platform()
	skConnections = connections.Connections('NOTIFICATIONS')
	token = skConnections.token
	uri = platform2.ws+'localhost:'+platform2.skPort+'/signalk/v1/stream?subscribe=none'
	if token:
		headers = {'Authorization': 'Bearer '+token}
		try:
			ws = create_connection(uri, header=headers, sslopt={"cert_reqs": ssl.CERT_NONE})
			ws.send('{"updates":[{"$source":"OpenPlotter.setNotification","values":[{"path":"'+sk+'","value":'+value+'}]}]}\n')
			ws.close()
		except Exception as e:
			sys.exit('Error connecting to Signal K server: '+str(e))
	else: checkConn()

def main():
	h = '''set-notification: set-notification [options] Signal_K_key (nominal|normal|alert|warn|alarm|emergency) ["message"]

    Sends a notification to the Signal K server
    
    Options:
      -h, --help	Shows this document.
      -n, --null	Sends "null". Ignores options, states and message. Only Signal_K_key is required.
      -s, --sound	Adds sound method.
      -v, --visual	Adds visual method.
    
    Exit Status:
    Returns success unless an error occurs.'''
	sk = ''
	state = ''
	message = ''
	method = []
	value = ''
	if len(sys.argv) < 3 and not '-h' in sys.argv and not '--help' in sys.argv: sys.exit('Error: wrong arguments')
	for idx,i in enumerate(sys.argv):
		if idx == 0: continue
		if i == '-h' or i == '--help':
			print(h)
			return
		elif i == '-n' or i == '--null': value = 'null'
		elif i == '-s' or i == '--sound': method.append("sound")
		elif i == '-v' or i == '--visual': method.append("visual")
		elif not sk: sk = i
		elif not state: state = i
		elif not message: message = i
		else: sys.exit('Error: wrong arguments')

	if not sk: sys.exit('Error: Signal K key not found')
	if not re.match('^[.0-9a-zA-Z]+$', sk): sys.exit('Error: not allowed characters in Signal K key')
	if not 'notifications.' in sk: sk = 'notifications.'+sk
	if value == 'null':
		send(sk,value)
		return
	if state == 'nominal' or state == 'normal' or state == 'alert' or state == 'warn' or state == 'alarm' or state == 'emergency': value = '{"state":"'+state+'",'
	else: sys.exit('Error: wrong state')
	value += '"message":"'+message.replace('"', "'")+'",'
	value += '"method":'+str(method).replace("'", '"')+'}'
	send(sk,value)
	return

if __name__ == '__main__':
	main()