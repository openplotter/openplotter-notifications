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

import wx, os, time, ujson
from openplotterSettings import conf
from openplotterSettings import platform
from openplotterSettings import language
import urllib.request

class MyFrame(wx.Frame):
	def __init__(self):
		self.platform = platform.Platform()
		self.conf = conf.Conf()
		self.currentLanguage = self.conf.get('GENERAL', 'lang')
		self.currentdir = os.path.dirname(os.path.abspath(__file__))
		self.language = language.Language(self.currentdir,'openplotter-notifications',self.currentLanguage)
		'''
		try: self.visualNormal = eval(self.conf.get('IOT', 'visualNormal'))
		except: self.visualNormal = (46, 52, 54, 255)
		try: self.visualAlert = eval(self.conf.get('IOT', 'visualAlert'))
		except: self.visualAlert = (32, 74, 135, 255)
		try: self.visualWarn = eval(self.conf.get('IOT', 'visualWarn'))
		except: self.visualWarn = (196, 160, 0, 255)
		try: self.visualAlarm = eval(self.conf.get('IOT', 'visualAlarm'))
		except: self.visualAlarm = (206, 92, 0, 255)
		try: self.visualEmergency = eval(self.conf.get('IOT', 'visualEmergency'))
		except: self.visualEmergency = (164, 0, 0, 255)

		wx.Frame.__init__(self, None, title=_('Notifications'), size=(800,475))
		self.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		icon = wx.Icon(self.currentdir+"/data/openplotter-iot.png", wx.BITMAP_TYPE_PNG)
		self.SetIcon(icon)

		panel = wx.Panel(self, wx.ID_ANY)

		self.listCurrent = wx.ListCtrl(panel, -1, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES, size=(-1,200))
		self.listCurrent.InsertColumn(0, _('Timestamp'), width=200)
		self.listCurrent.InsertColumn(1, _('state'), width=100)
		self.listCurrent.InsertColumn(2, 'Signal K Key', width=200)
		self.listCurrent.InsertColumn(3, _('message'), width=300)
		self.listCurrent.SetTextColour(wx.BLACK)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(self.listCurrent, 1, wx.EXPAND)
		panel.SetSizer(vbox)

		self.playing = False
		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.refresh, self.timer)
		self.timer.Start(1000)

		self.Centre()
		'''
	'''	
	def refresh(self,e):
		try:
			req = urllib.request.Request(self.platform.http+'localhost:'+self.platform.skPort+'/signalk/v1/api/vessels/self/notifications')
			content = urllib.request.urlopen(req).read()
			self.data = ujson.loads(content)
			self.listCurrent.DeleteAllItems()
		except: self.data = {}
		leaves = list(self.walk_json(self.data))
		notifications = {}
		for i in leaves:
			path = ''
			for ii in i:
				nextItem = i.index(ii)+1
				if ii == '$source':
					if not path in notifications: notifications[path] = {}
					break
				if ii == 'timestamp':
					if not path in notifications: notifications[path] = {}
					break
				elif ii == 'value': 
					if not path in notifications: notifications[path] = {}
					if i[nextItem] == None: break
					if i[nextItem] == 'state': notifications[path]['state'] = i[nextItem+1]
					if i[nextItem] == 'timestamp': notifications[path]['timestamp'] = i[nextItem+1]
					if i[nextItem] == 'message': notifications[path]['message'] = i[nextItem+1]
					if i[nextItem] == 'method': notifications[path]['method'] = i[nextItem+1]
					break
				else:
					if path: path += '.'+ii
					else: path = ii
		if notifications:
			for i in notifications:
				if 'method' in notifications[i] and notifications[i]['method']:
					item = self.listCurrent.InsertItem(0, notifications[i]['timestamp'])
					self.listCurrent.SetItem(item, 1, notifications[i]['state'])
					self.listCurrent.SetItem(item, 2, i)
					if 'message' in notifications[i]:
						self.listCurrent.SetItem(item, 3, notifications[i]['message'])
					if notifications[i]['state'] == 'normal': self.listCurrent.SetItemTextColour(item,self.visualNormal)
					elif notifications[i]['state'] == 'alert': self.listCurrent.SetItemTextColour(item,self.visualAlert)
					elif notifications[i]['state'] == 'warn': self.listCurrent.SetItemTextColour(item,self.visualWarn)
					elif notifications[i]['state'] == 'alarm': self.listCurrent.SetItemTextColour(item,self.visualAlarm)
					elif notifications[i]['state'] == 'emergency': self.listCurrent.SetItemTextColour(item,self.visualEmergency)

		if self.listCurrent.GetItemCount() == 0:
			self.timer.Stop()
			self.Destroy()

	def walk_json(self, tree, path=[]):
		try:
			for root, child in tree.items():
				yield from self.walk_json(child, path + [root])
		except AttributeError:
			yield path + [tree]
	'''
	
def main():
	app = wx.App()
	MyFrame().Show()
	#time.sleep(1)
	app.MainLoop()

if __name__ == '__main__':
	main()
