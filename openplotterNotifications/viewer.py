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

import wx, os, requests, ujson
from openplotterSettings import conf
from openplotterSettings import language
from openplotterSettings import platform

class MyFrame(wx.Frame):
	def __init__(self):
		self.conf = conf.Conf()
		self.conf_folder = self.conf.conf_folder
		if self.conf.get('GENERAL', 'debug') == 'yes': self.debug = True
		else: self.debug = False
		self.platform = platform.Platform()
		self.currentdir = os.path.dirname(os.path.abspath(__file__))
		self.currentLanguage = self.conf.get('GENERAL', 'lang')
		self.language = language.Language(self.currentdir,'openplotter-notifications',self.currentLanguage)

		try: self.colorNominal = eval(self.conf.get('NOTIFICATIONS', 'visualNominal'))
		except: self.colorNominal = [(0, 181, 30, 255),True]
		try: self.colorNormal = eval(self.conf.get('NOTIFICATIONS', 'visualNormal'))
		except: self.colorNormal= [(46, 52, 54, 255),True]
		try: self.colorAlert= eval(self.conf.get('NOTIFICATIONS', 'visualAlert'))
		except: self.colorAlert = [(32, 74, 135, 255),True]
		try: self.colorWarn = eval(self.conf.get('NOTIFICATIONS', 'visualWarn'))
		except: self.colorWarn = [(196, 160, 0, 255),True]
		try: self.colorAlarm = eval(self.conf.get('NOTIFICATIONS', 'visualAlarm'))
		except: self.colorAlarm = [(206, 92, 0, 255),False]
		try: self.colorEmergency = eval(self.conf.get('NOTIFICATIONS', 'visualEmergency'))
		except: self.colorEmergency = [(164, 0, 0, 255),False]

		wx.Frame.__init__(self, None, title=_('Notifications viewer'), size=(800,444))
		self.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		icon = wx.Icon(self.currentdir+"/data/openplotter-notifications-viewer.png", wx.BITMAP_TYPE_PNG)
		self.SetIcon(icon)

		self.toolbar1 = wx.ToolBar(self, style=wx.TB_TEXT)
		self.filterVesselLabel = wx.StaticText(self.toolbar1, 101, label=_('Vessel'))
		filterVesselLabel = self.toolbar1.AddControl(self.filterVesselLabel)
		self.filterVessel = wx.TextCtrl(self.toolbar1, 102)
		filterVessel = self.toolbar1.AddControl(self.filterVessel)
		self.filterNotiLabel = wx.StaticText(self.toolbar1, 103, label=_('Notification'))
		filterNotiLabel = self.toolbar1.AddControl(self.filterNotiLabel)
		self.filterNoti = wx.TextCtrl(self.toolbar1, 104)
		filterNoti = self.toolbar1.AddControl(self.filterNoti)
		self.filterStateLabel = wx.StaticText(self.toolbar1, 105, label=_('State'))
		filterStateLabel = self.toolbar1.AddControl(self.filterStateLabel)
		self.filterState = wx.TextCtrl(self.toolbar1, 106)
		filterState = self.toolbar1.AddControl(self.filterState)
		self.filterMessageLabel = wx.StaticText(self.toolbar1, 107, label=_('Message'))
		filterMessageLabel = self.toolbar1.AddControl(self.filterMessageLabel)
		self.filterMessage = wx.TextCtrl(self.toolbar1, 108)
		filterMessage = self.toolbar1.AddControl(self.filterMessage)
		filter2 = self.toolbar1.AddTool(109, _('Filter'), wx.Bitmap(self.currentdir+"/data/filter.png"))
		self.Bind(wx.EVT_TOOL, self.onFilter, filter2)
		reset = self.toolbar1.AddTool(110, _('Reset'), wx.Bitmap(self.currentdir+"/data/refresh.png"))
		self.Bind(wx.EVT_TOOL, self.onReset, reset)

		self.list = wx.ListCtrl(self, -1, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES)
		self.list.InsertColumn(0, _('Vessel'), width=130)
		self.list.InsertColumn(1, _('Notification'), width=190)
		self.list.InsertColumn(2, _('state'), width=90)
		self.list.InsertColumn(3, _('Message'), width=175)
		self.list.InsertColumn(4, _('Timestamp'), width=175)
		self.list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.onListActivated)
		self.list.SetTextColour(wx.BLACK)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(self.toolbar1, 0, wx.EXPAND)
		vbox.Add(self.list , 1, wx.ALL | wx.EXPAND, 5)
		self.SetSizer(vbox)

		maxi = self.conf.get('GENERAL', 'maximize')
		if maxi == '1': self.Maximize()

		self.Centre()

		self.onReset()
		self.refresh()

		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.refresh, self.timer)
		self.timer.Start(2000)

	def onListActivated(self,e):
		selected = self.list.GetFirstSelected()
		if selected == -1: return
		noti = self.list.GetItemText(selected, 1)
		show = ''
		for i in self.notilist:
			if noti == i[1]: show = i
		if show:
			dlg = showDetails(show)
			res = dlg.ShowModal()
			dlg.Destroy()

	def onReset(self, e=0):
		self.filterVessel.SetValue('')
		self.filterNoti.SetValue('')
		self.filterState.SetValue('')
		self.filterMessage.SetValue('')
		self.filterVessel2 = ''
		self.filterNoti2 = ''
		self.filterState2 = ''
		self.filterMessage2 = ''
		self.list.DeleteAllItems()

	def onFilter(self, e=0):
		self.filterVessel2 = self.filterVessel.GetValue()
		self.filterNoti2 = self.filterNoti.GetValue()
		self.filterState2 = self.filterState.GetValue()
		self.filterMessage2 = self.filterMessage.GetValue()
		self.list.DeleteAllItems()

	def onClose(self,e):
		self.timer.Stop()
		self.Destroy()

	def applyFilters(self,data):
		o = [True,True,True,True]
		if self.filterVessel2: 
			if self.filterVessel2 in data[0]: o[0] = True
			else: o[0] = False
		if self.filterNoti2: 
			if self.filterNoti2 in data[1]: o[1] = True
			else: o[1] = False
		if self.filterState2: 
			if self.filterState2 in data[2]: o[2] = True
			else: o[2] = False
		if self.filterMessage2: 
			if self.filterMessage2 in data[3]: o[3] = True
			else: o[3] = False
		if o[0] == True and o[1] == True and o[2] == True and o[3] == True: return True
		else: return False

	def refresh(self,e=0):
		notilist = []
		try:
			resp = requests.get(self.platform.http+'localhost:'+self.platform.skPort+'/signalk/v1/api/', verify=False)
			data = ujson.loads(resp.content)
		except: data = {}

		if 'self' in data: uuid = data['self'].replace('vessels.','')
		else: uuid = ''

		if 'vessels' in data:
			for i in data['vessels']:
				if uuid == i:
					if 'name' in data['vessels'][i] and data['vessels'][i]['name']: i2 = data['vessels'][i]['name']
					else: i2 = 'Self'
				else:
					if 'name' in data['vessels'][i] and data['vessels'][i]['name']: i2 = data['vessels'][i]['name']
					else:
						i2 = i.replace('urn:mrn:imo:', '')
						i2 = i2.replace('urn:mrn:signalk:', '')
				if 'notifications' in data['vessels'][i]:
					c = True
					while c:
						c = False
						for ii in list(data['vessels'][i]['notifications']):
							if 'meta' in data['vessels'][i]['notifications'][ii]:
								c = True
								try: del data['vessels'][i]['notifications'][ii]['meta']
								except: pass
							if 'values' in data['vessels'][i]['notifications'][ii]:
								c = True
								try: del data['vessels'][i]['notifications'][ii]['values']
								except: pass
							if 'value' in data['vessels'][i]['notifications'][ii] and 'timestamp' in data['vessels'][i]['notifications'][ii] and '$source' in data['vessels'][i]['notifications'][ii]:
								if data['vessels'][i]['notifications'][ii]['value'] and 'state' in data['vessels'][i]['notifications'][ii]['value'] and 'message' in data['vessels'][i]['notifications'][ii]['value'] and 'method' in data['vessels'][i]['notifications'][ii]['value']:
									item = (i2,ii,data['vessels'][i]['notifications'][ii]['value']['state'],data['vessels'][i]['notifications'][ii]['value']['message'],data['vessels'][i]['notifications'][ii]['timestamp'],data['vessels'][i]['notifications'][ii]['$source'],data['vessels'][i]['notifications'][ii]['value']['method'])
									if self.applyFilters(item): notilist.append(item)
								elif not data['vessels'][i]['notifications'][ii]['value']:
									item = (i2,ii,'','',data['vessels'][i]['notifications'][ii]['timestamp'],data['vessels'][i]['notifications'][ii]['$source'],'')
									if self.applyFilters(item): notilist.append(item)
								c = True
								try:
									del data['vessels'][i]['notifications'][ii]['value']
									del data['vessels'][i]['notifications'][ii]['$source']
									del data['vessels'][i]['notifications'][ii]['timestamp']
								except: pass
							else:
								for iii in data['vessels'][i]['notifications'][ii]:
									c = True
									try: data['vessels'][i]['notifications'][ii+'.'+iii] = data['vessels'][i]['notifications'][ii][iii]
									except: pass
								del data['vessels'][i]['notifications'][ii]

		
		self.notilist = sorted(notilist, key=lambda timestamp: timestamp[4],reverse=True)

		reloading = False
		for i in self.notilist:
			exists = False
			if i[2] == 'nominal': color = self.colorNominal[0]
			elif i[2] == 'normal': color = self.colorNormal[0]
			elif i[2] == 'alert': color = self.colorAlert[0]
			elif i[2] == 'warn': color = self.colorWarn[0]
			elif i[2] == 'alarm': color = self.colorAlarm[0]
			elif i[2] == 'emergency': color = self.colorEmergency[0]
			else: color = wx.BLACK
			timestamp = i[4].replace('T',' ')
			timestamp = timestamp.replace('Z','')
			for ii in range(self.list.GetItemCount()):
				if self.list.GetItemText(ii, 0) == i[0] and self.list.GetItemText(ii, 1) == i[1]:
					exists = True
					self.list.SetItem(ii,2,i[2])
					self.list.SetItem(ii,3,i[3])
					self.list.SetItem(ii,4,timestamp)
					self.list.SetItemTextColour(ii,color)
			if not exists:
				reloading = True
				break

		if reloading:
			self.list.DeleteAllItems()
			for i in self.notilist:
				if i[2] == 'nominal': color = self.colorNominal[0]
				elif i[2] == 'normal': color = self.colorNormal[0]
				elif i[2] == 'alert': color = self.colorAlert[0]
				elif i[2] == 'warn': color = self.colorWarn[0]
				elif i[2] == 'alarm': color = self.colorAlarm[0]
				elif i[2] == 'emergency': color = self.colorEmergency[0]
				else: color = wx.BLACK
				timestamp = i[4].replace('T',' ')
				timestamp = timestamp.replace('Z','')
				self.list.Append([i[0],i[1],i[2],i[3],timestamp])
				self.list.SetItemTextColour(self.list.GetItemCount()-1,color)

################################################################################

class showDetails(wx.Dialog):

	def __init__(self, noti):

		self.conf = conf.Conf()
		self.currentLanguage = self.conf.get('GENERAL', 'lang')
		if self.conf.get('GENERAL', 'debug') == 'yes': self.debug = True
		else: self.debug = False

		wx.Dialog.__init__(self, None, title=_('Notification details'), size=(550, 320))
		self.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		panel = wx.Panel(self)

		font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_BOLD)

		vesselLabel = wx.StaticText(panel, label = _('Vessel'))
		vesselLabel.SetForegroundColour((60,60,60,255))
		vesselLabel.SetFont(font)
		vessel = wx.StaticText(panel, label = noti[0])

		notificationLabel = wx.StaticText(panel, label = _('Notification'))
		notificationLabel.SetForegroundColour((60,60,60,255))
		notificationLabel.SetFont(font)
		notificacion = wx.StaticText(panel, label = 'notifications.'+noti[1])

		stateLabel = wx.StaticText(panel, label = _('State'))
		stateLabel.SetForegroundColour((60,60,60,255))
		stateLabel.SetFont(font)
		state = wx.StaticText(panel, label = noti[2])

		messageLabel = wx.StaticText(panel, label = _('Message'))
		messageLabel.SetForegroundColour((60,60,60,255))
		messageLabel.SetFont(font)
		message = wx.StaticText(panel, label = noti[3])

		methodLabel = wx.StaticText(panel, label = _('Method'))
		methodLabel.SetForegroundColour((60,60,60,255))
		methodLabel.SetFont(font)
		method = wx.StaticText(panel, label = str(noti[6]))

		sourceLabel = wx.StaticText(panel, label = _('Source'))
		sourceLabel.SetForegroundColour((60,60,60,255))
		sourceLabel.SetFont(font)
		source = wx.StaticText(panel, label = noti[5])

		timestampLabel = wx.StaticText(panel, label = _('Timestamp'))
		timestampLabel.SetForegroundColour((60,60,60,255))
		timestampLabel.SetFont(font)
		timestamp = wx.StaticText(panel, label = noti[4])

		close = wx.Button(panel, label=_('Close'))
		close.Bind(wx.EVT_BUTTON, self.onClose)

		vbox1 = wx.BoxSizer(wx.VERTICAL)
		vbox1.Add(stateLabel, 1, wx.LEFT | wx.EXPAND, 10)
		vbox1.AddSpacer(5)
		vbox1.Add(state, 1, wx.LEFT | wx.EXPAND, 10)

		vbox2 = wx.BoxSizer(wx.VERTICAL)
		vbox2.Add(methodLabel, 1, wx.LEFT | wx.EXPAND, 10)
		vbox2.AddSpacer(5)
		vbox2.Add(method, 1, wx.LEFT | wx.EXPAND, 10)

		hbox1 = wx.BoxSizer(wx.HORIZONTAL)
		hbox1.Add(vbox1, 1, wx.ALL | wx.EXPAND, 0)
		hbox1.Add(vbox2, 1, wx.ALL | wx.EXPAND, 0)

		vbox3 = wx.BoxSizer(wx.VERTICAL)
		vbox3.Add(timestampLabel, 1, wx.LEFT | wx.EXPAND, 10)
		vbox3.AddSpacer(5)
		vbox3.Add(timestamp, 1, wx.LEFT | wx.EXPAND, 10)

		vbox4 = wx.BoxSizer(wx.VERTICAL)
		vbox4.Add(sourceLabel, 1, wx.LEFT | wx.EXPAND, 10)
		vbox4.AddSpacer(5)
		vbox4.Add(source, 1, wx.LEFT | wx.EXPAND, 10)

		hbox2 = wx.BoxSizer(wx.HORIZONTAL)
		hbox2.Add(vbox3, 1, wx.ALL | wx.EXPAND, 0)
		hbox2.Add(vbox4, 1, wx.ALL | wx.EXPAND, 0)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.AddSpacer(10)
		vbox.Add(vesselLabel, 1, wx.LEFT, 10)
		vbox.AddSpacer(5)
		vbox.Add(vessel, 1, wx.LEFT, 10)
		vbox.AddSpacer(5)
		vbox.Add(notificationLabel, 1, wx.LEFT, 10)
		vbox.AddSpacer(5)
		vbox.Add(notificacion, 1, wx.LEFT, 10)
		vbox.AddSpacer(5)
		vbox.Add(messageLabel, 1, wx.LEFT, 10)
		vbox.AddSpacer(5)
		vbox.Add(message, 1, wx.LEFT, 10)
		vbox.AddSpacer(5)
		vbox.Add(hbox1, 1, wx.ALL | wx.EXPAND, 0)
		vbox.AddSpacer(5)
		vbox.Add(hbox2, 1, wx.ALL | wx.EXPAND, 0)
		vbox.AddStretchSpacer(1)
		vbox.Add(close, 1, wx.ALL | wx.EXPAND, 10)
		panel.SetSizer(vbox)

	def onClose(self,e=0):
		self.Destroy()

################################################################################

def main():
	app = wx.App()
	MyFrame().Show()
	app.MainLoop()

if __name__ == '__main__':
	main()