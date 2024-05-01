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

import wx, sys, os, ujson, requests
import wx.richtext as rt
from openplotterSettings import conf
from openplotterSettings import platform
from openplotterSettings import language

class MyFrame(wx.Frame):
	def __init__(self):
		self.platform = platform.Platform()
		self.conf = conf.Conf()
		self.currentLanguage = self.conf.get('GENERAL', 'lang')
		self.currentdir = os.path.dirname(os.path.abspath(__file__))
		self.language = language.Language(self.currentdir,'openplotter-notifications',self.currentLanguage)

		wx.Frame.__init__(self, None, title=_('Notifications'), size=(400,300))
		self.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		icon = wx.Icon(self.currentdir+"/data/openplotter-notifications.png", wx.BITMAP_TYPE_PNG)
		self.SetIcon(icon)

		panel = wx.Panel(self, wx.ID_ANY)

		self.state = sys.argv[2]
		state = wx.StaticText(panel, label = self.state)
		self.path = sys.argv[1]
		path = wx.StaticText(panel, label = self.path)
		message = rt.RichTextCtrl(panel)
		message.SetMargins((10,10))
		message.BeginAlignment(wx.TEXT_ALIGNMENT_CENTRE)
		message.WriteText(sys.argv[3])
		message.EndAlignment()
		message.ShowPosition(0)
		self.timestamp = sys.argv[4]
		timestamp = wx.StaticText(panel, label = self.timestamp)

		if self.state == 'nominal':
			try: color = eval(self.conf.get('NOTIFICATIONS', 'visualNominal'))
			except: color = [(0, 181, 30, 255),True]
		elif self.state == 'normal':
			try: color = eval(self.conf.get('NOTIFICATIONS', 'visualNormal'))
			except: color = [(46, 52, 54, 255),True]
		elif self.state == 'alert':
			try: color = eval(self.conf.get('NOTIFICATIONS', 'visualAlert'))
			except: color = [(32, 74, 135, 255),True]
		elif self.state == 'warn':
			try: color = eval(self.conf.get('NOTIFICATIONS', 'visualWarn'))
			except: color = [(196, 160, 0, 255),True]
		elif self.state == 'alarm':
			try: color = eval(self.conf.get('NOTIFICATIONS', 'visualAlarm'))
			except: color = [(206, 92, 0, 255),False]
		elif self.state == 'emergency':
			try: color = eval(self.conf.get('NOTIFICATIONS', 'visualEmergency'))
			except: color = [(164, 0, 0, 255),False]
		state.SetForegroundColour(color[0])
		font = wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.ITALIC, wx.BOLD)
		state.SetFont(font)

		close = wx.Button(panel, label=_('Close'))
		close.Bind(wx.EVT_BUTTON, self.onClose)

		hbox1 = wx.BoxSizer(wx.HORIZONTAL)
		hbox1.AddStretchSpacer(1)
		hbox1.Add(state, 0, wx.ALL | wx.EXPAND, 0)
		hbox1.AddStretchSpacer(1)

		hbox2 = wx.BoxSizer(wx.HORIZONTAL)
		hbox2.AddStretchSpacer(1)
		hbox2.Add(path, 0, wx.ALL | wx.EXPAND, 0)
		hbox2.AddStretchSpacer(1)

		hbox3 = wx.BoxSizer(wx.HORIZONTAL)
		hbox3.AddStretchSpacer(1)
		hbox3.Add(timestamp, 0, wx.ALL | wx.EXPAND, 0)
		hbox3.AddStretchSpacer(1)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.AddSpacer(5)
		vbox.Add(hbox1, 0, wx.ALL | wx.EXPAND, 5)
		vbox.Add(hbox2, 0, wx.ALL | wx.EXPAND, 5)
		vbox.Add(hbox3, 0, wx.ALL | wx.EXPAND, 5)
		vbox.Add(message, 1, wx.ALL | wx.EXPAND, 5)
		vbox.Add(close, 0, wx.ALL | wx.EXPAND, 10)
		panel.SetSizer(vbox)

		if color[1]:
			self.timer = wx.Timer(self)
			self.Bind(wx.EVT_TIMER, self.refresh, self.timer)
			self.timer.Start(3000)
		else: self.timer = False

		self.Centre()

	def onClose(self,e=0):
		if self.timer: self.timer.Stop()
		self.Destroy()

	def refresh(self,e):
		try:
			path = self.path.replace('.','/')
			resp = requests.get(self.platform.http+'localhost:'+self.platform.skPort+'/signalk/v1/api/vessels/self/'+path, verify=False)
			data = ujson.loads(resp.content)
		except: data = {}
		if 'value' in data:
			if not data['value']: self.onClose()
			elif 'state' in data['value']:
				if data['value']['state'] != self.state: self.onClose()
				else:
					if 'timestamp' in data:
						if data['timestamp'] != self.timestamp: self.onClose()
					else: self.onClose()
			else: self.onClose()
		else: self.onClose()
	
def main():
	app = wx.App()
	MyFrame().Show()
	app.MainLoop()

if __name__ == '__main__':
	main()
