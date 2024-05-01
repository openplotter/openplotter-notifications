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

import wx, os, sys, webbrowser, subprocess, time, ujson, re, requests, ujson
import wx.richtext as rt
from openplotterSettings import conf
from openplotterSettings import language
from openplotterSettings import platform
from openplotterSettings import selectKey
from .version import version

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

		wx.Frame.__init__(self, None, title='Notifications '+version, size=(800,444))
		self.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		icon = wx.Icon(self.currentdir+"/data/openplotter-notifications.png", wx.BITMAP_TYPE_PNG)
		self.SetIcon(icon)
		self.CreateStatusBar()
		font_statusBar = self.GetStatusBar().GetFont()
		font_statusBar.SetWeight(wx.BOLD)
		self.GetStatusBar().SetFont(font_statusBar)

		self.toolbar1 = wx.ToolBar(self, style=wx.TB_TEXT)
		toolHelp = self.toolbar1.AddTool(101, _('Help'), wx.Bitmap(self.currentdir+"/data/help.png"))
		self.Bind(wx.EVT_TOOL, self.OnToolHelp, toolHelp)
		if not self.platform.isInstalled('openplotter-doc'): self.toolbar1.EnableTool(101,False)
		toolSettings = self.toolbar1.AddTool(102, _('Settings'), wx.Bitmap(self.currentdir+"/data/settings.png"))
		self.Bind(wx.EVT_TOOL, self.OnToolSettings, toolSettings)
		self.toolbar1.AddSeparator()
		refresh = self.toolbar1.AddTool(103, _('Refresh'), wx.Bitmap(self.currentdir+"/data/refresh.png"))
		self.Bind(wx.EVT_TOOL, self.onRefresh, refresh)

		self.notebook = wx.Notebook(self)
		self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onTabChange)
		self.summary = wx.Panel(self.notebook)
		self.visualMethod = wx.Panel(self.notebook)
		self.soundMethod = wx.Panel(self.notebook)
		self.actions = wx.Panel(self.notebook)
		self.custom = wx.Panel(self.notebook)
		self.notebook.AddPage(self.custom, _('Send'))
		self.notebook.AddPage(self.summary, _('Zones'))
		self.notebook.AddPage(self.actions, _('Actions'))
		self.notebook.AddPage(self.visualMethod, _('Visual'))
		self.notebook.AddPage(self.soundMethod, _('Sound'))

		self.il = wx.ImageList(24, 24)
		img0 = self.il.Add(wx.Bitmap(self.currentdir+"/data/notifications.png", wx.BITMAP_TYPE_PNG))
		img1 = self.il.Add(wx.Bitmap(self.currentdir+"/data/sk.png", wx.BITMAP_TYPE_PNG))
		img2 = self.il.Add(wx.Bitmap(self.currentdir+"/data/openplotter-24.png", wx.BITMAP_TYPE_PNG))
		img3 = self.il.Add(wx.Bitmap(self.currentdir+"/data/visual.png", wx.BITMAP_TYPE_PNG))
		img4 = self.il.Add(wx.Bitmap(self.currentdir+"/data/play.png", wx.BITMAP_TYPE_PNG))

		self.notebook.AssignImageList(self.il)
		self.notebook.SetPageImage(0, img0)
		self.notebook.SetPageImage(1, img1)
		self.notebook.SetPageImage(2, img2)
		self.notebook.SetPageImage(3, img3)
		self.notebook.SetPageImage(4, img4)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(self.toolbar1, 0, wx.EXPAND)
		vbox.Add(self.notebook, 1, wx.EXPAND)
		self.SetSizer(vbox)

		self.pageCustom()
		self.pageSummary()
		self.pageActions()
		self.pageVisual()
		self.pageSound()

		self.onRefresh()

		maxi = self.conf.get('GENERAL', 'maximize')
		if maxi == '1': self.Maximize()

		self.Centre()

		self.readCustom() #force

	def ShowStatusBar(self, w_msg, colour):
		self.GetStatusBar().SetForegroundColour(colour)
		self.SetStatusText(w_msg)

	def ShowStatusBarRED(self, w_msg):
		self.ShowStatusBar(w_msg, (130,0,0))

	def ShowStatusBarGREEN(self, w_msg):
		self.ShowStatusBar(w_msg, (0,130,0))

	def ShowStatusBarBLACK(self, w_msg):
		self.ShowStatusBar(w_msg, wx.BLACK) 

	def ShowStatusBarYELLOW(self, w_msg):
		self.ShowStatusBar(w_msg,(255,140,0)) 

	def onTabChange(self, event):
		try:
			self.SetStatusText('')
		except:pass

	def OnToolHelp(self, event): 
		url = "/usr/share/openplotter-doc/notifications/notifications_app.html"
		webbrowser.open(url, new=2)

	def OnToolSettings(self, event=0): 
		subprocess.call(['pkill', '-f', 'openplotter-settings'])
		subprocess.Popen('openplotter-settings')

	def restartRead(self):
		subprocess.call(['systemctl', '--user', 'restart', 'openplotter-notifications-read.service'])
		self.ShowStatusBarGREEN(_('Notifications service restarted'))

	def onRefresh(self, e=0):
		self.readCustom()
		self.OnReadThresholds()
		self.readNotifications()
		self.readColours()
		self.readSounds()

		self.ShowStatusBarBLACK(' ')

	############################################################################

	def pageCustom(self):
		self.listCustom = wx.ListCtrl(self.custom, -1, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES, size=(-1,200))
		self.listCustom.InsertColumn(0, _('Notification'), width=320)
		self.listCustom.InsertColumn(1, _('State'), width=90)
		self.listCustom.InsertColumn(2, _('Method'), width=125)
		self.listCustom.InsertColumn(3, _('Message'), width=210)
		self.listCustom.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onListCustomSelected)
		self.listCustom.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onlistCustomDeselected)
		self.listCustom.SetTextColour(wx.BLACK)

		self.toolbar8 = wx.ToolBar(self.custom, style=wx.TB_VERTICAL)
		self.toolbar8.AddSeparator()
		startCustom = self.toolbar8.AddTool(804, _('Trigger'), wx.Bitmap(self.currentdir+"/data/start.png"))
		self.Bind(wx.EVT_TOOL, self.onStartCustom, startCustom)
		stopCustom = self.toolbar8.AddTool(805, _('Stop'), wx.Bitmap(self.currentdir+"/data/stop.png"))
		self.Bind(wx.EVT_TOOL, self.onStopCustom, stopCustom)
		self.toolbar8.AddSeparator()
		addCustom = self.toolbar8.AddTool(801, _('Add'), wx.Bitmap(self.currentdir+"/data/add.png"))
		self.Bind(wx.EVT_TOOL, self.onAddCustom, addCustom)
		toolEdit = self.toolbar8.AddTool(802, _('Edit'), wx.Bitmap(self.currentdir+"/data/edit.png"))
		self.Bind(wx.EVT_TOOL, self.onEditCustom, toolEdit)
		toolDelete = self.toolbar8.AddTool(803, _('Delete'), wx.Bitmap(self.currentdir+"/data/cancel.png"))
		self.Bind(wx.EVT_TOOL, self.onDeleteCustom, toolDelete)
		self.toolbar8.AddSeparator()

		hbox1 = wx.BoxSizer(wx.HORIZONTAL)
		hbox1.Add(self.listCustom , 1, wx.ALL | wx.EXPAND, 0)
		hbox1.Add(self.toolbar8 , 0, wx.EXPAND, 0)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(hbox1, 1, wx.EXPAND, 0)
		self.custom.SetSizer(vbox)

	def getColour(self, state):
		if state == 'nominal': return self.visualNominal.GetColour()
		elif state == 'normal': return self.visualNormal.GetColour()
		elif state == 'alert': return self.visualAlert.GetColour()
		elif state == 'warn': return self.visualWarn.GetColour()
		elif state == 'alarm': return self.visualAlarm.GetColour()
		elif state == 'emergency': return self.visualEmergency.GetColour()

	def readCustom(self):
		self.onlistCustomDeselected()
		self.listCustom.DeleteAllItems()
		try: self.customList = eval(self.conf.get('NOTIFICATIONS', 'customNot'))
		except: self.customList = []
		for i in self.customList:
			self.listCustom.Append([i['key'],i['state'],str(i['method']),i['message']])

		listCount = range(self.listCustom.GetItemCount())
		for i in listCount:
			try:
				path = self.listCustom.GetItemText(i, 0)
				state = self.listCustom.GetItemText(i, 1)
				message = self.listCustom.GetItemText(i, 3)
				path = path.replace('.','/')
				resp = requests.get(self.platform.http+'localhost:'+self.platform.skPort+'/signalk/v1/api/vessels/self/'+path+'/value', verify=False)
				result = ujson.loads(resp.content)
				if 'state' in result:
					if result['state'] == state:
						if 'message' in result:
							if result['message'] == message:
								self.listCustom.SetItemTextColour(i,self.getColour(state))
			except: pass

	def onListCustomSelected(self, e):
		self.onlistCustomDeselected()
		selected = self.listCustom.GetFirstSelected()
		if selected == -1: return
		index = self.listCustom.GetItemText(selected, 0)
		self.toolbar8.EnableTool(802,True)
		self.toolbar8.EnableTool(803,True)
		self.toolbar8.EnableTool(804,True)
		self.toolbar8.EnableTool(805,True)

	def onlistCustomDeselected(self, event=0):
		self.toolbar8.EnableTool(802,False)
		self.toolbar8.EnableTool(803,False)
		self.toolbar8.EnableTool(804,False)
		self.toolbar8.EnableTool(805,False)

	def onAddCustom(self,e):
		edit = {}
		self.setCustom(edit)

	def setCustom(self,edit):
		dlg = editCustom(edit)
		res = dlg.ShowModal()
		if res == wx.ID_OK:
			key = dlg.keyResult
			state = dlg.state.GetValue()
			message = dlg.message.GetValue()
			visual = dlg.visual.GetValue()
			sound = dlg.sound.GetValue()
			method = []
			if visual: method.append('visual')
			if sound: method.append('sound')
			if edit:
				self.customList[edit['selected']] = {'key':key,'state':state,'method':str(method),'message':message}
			else:
				self.customList.append({'key':key,'state':state,'method':str(method),'message':message})
			self.conf.set('NOTIFICATIONS', 'customNot', str(self.customList))
			self.onRefresh()
		dlg.Destroy()

	def onEditCustom(self,e):
		selected = self.listCustom.GetFirstSelected()
		if selected == -1: return
		key = self.listCustom.GetItemText(selected, 0)
		state = self.listCustom.GetItemText(selected, 1)
		method = eval(self.listCustom.GetItemText(selected, 2))
		message = self.listCustom.GetItemText(selected, 3)
		edit = {'selected':selected,'key':key,'state':state,'method':method,'message':message}
		self.setCustom(edit)

	def onDeleteCustom(self,e):
		selected = self.listCustom.GetFirstSelected()
		if selected == -1: return
		del self.customList[selected]
		self.conf.set('NOTIFICATIONS', 'customNot', str(self.customList))
		self.onRefresh()

	def onStartCustom(self,e):
		selected = self.listCustom.GetFirstSelected()
		if selected == -1: return
		key = self.listCustom.GetItemText(selected, 0)
		state = self.listCustom.GetItemText(selected, 1)
		message = self.listCustom.GetItemText(selected, 3)
		sound = False
		visual = False
		try: method = eval(self.listCustom.GetItemText(selected, 2))
		except: method = []
		if 'visual' in method: visual = True
		if 'sound' in method: sound = True
		command = ['set-notification']
		if sound: command.append('-s')
		if visual: command.append('-v')
		command.append(key)
		command.append(state)
		command.append(message)
		process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = process.communicate()
		if err:
			if self.debug:
				err = err.decode()
				err = err.replace('\n','')
				print('Error setting notification: '+str(err))
		self.onRefresh()

	def onStopCustom(self,e):
		selected = self.listCustom.GetFirstSelected()
		if selected == -1: return
		key = self.listCustom.GetItemText(selected, 0)
		command = ['set-notification']
		command.append('-n')
		command.append(key)
		process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = process.communicate()
		if err:
			if self.debug:
				err = err.decode()
				err = err.replace('\n','')
				print('Error setting notification: '+str(err))
		self.onRefresh()

	############################################################################

	def pageSummary(self):
		self.summaryLogger = rt.RichTextCtrl(self.summary, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_DONTWRAP|wx.LC_SORT_ASCENDING)
		self.summaryLogger.SetMargins((10,10))

		self.toolbar3 = wx.ToolBar(self.summary, style= wx.TB_VERTICAL)
		self.toolbar3.AddSeparator()
		toolThresholds = self.toolbar3.AddTool(301, _('Edit'), wx.Bitmap(self.currentdir+"/data/edit.png"))
		self.Bind(wx.EVT_TOOL, self.OnToolThresholds, toolThresholds)
		self.toolbar3.AddSeparator()

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(self.summaryLogger, 1, wx.EXPAND, 0)
		sizer.Add(self.toolbar3, 0,  wx.EXPAND, 0)
		self.summary.SetSizer(sizer)

	def OnToolThresholds(self, e):
		if self.platform.skPort: 
			url = self.platform.http+'localhost:'+self.platform.skPort+'/admin/#/serverConfiguration/plugins/zones-edit'
			webbrowser.open(url, new=2)

	def OnReadThresholds(self):
		self.summaryLogger.Clear()
		try: visualNominal = eval(self.conf.get('NOTIFICATIONS', 'visualNominal'))
		except: visualNominal = [(0, 181, 30, 255), True]
		try: visualNormal = eval(self.conf.get('NOTIFICATIONS', 'visualNormal'))
		except: visualNormal = [(46, 52, 54, 255), True]
		try: visualAlert = eval(self.conf.get('NOTIFICATIONS', 'visualAlert'))
		except: visualAlert = [(32, 74, 135, 255), True]
		try: visualWarn = eval(self.conf.get('NOTIFICATIONS', 'visualWarn'))
		except: visualWarn = [(196, 160, 0, 255), True]
		try: visualAlarm = eval(self.conf.get('NOTIFICATIONS', 'visualAlarm'))
		except: visualAlarm = [(206, 92, 0, 255), True]
		try: visualEmergency = eval(self.conf.get('NOTIFICATIONS', 'visualEmergency'))
		except: visualEmergency = [(164, 0, 0, 255), True]
		file = self.platform.skDir+'/plugin-config-data/zones-edit.json'
		try:
			with open(file) as data_file:
				data = ujson.load(data_file)
				if not data['enabled']:
					self.summaryLogger.WriteText(_('Signal K Zones plugin is disabled'))
					return
		except:
			self.summaryLogger.WriteText(_('Error reading Signal K Zones configuration. Is this plugin installed and enabled?'))
			return
		if 'zones' in data['configuration']:
			for item in data['configuration']['zones']:
				if item['key']:
					self.summaryLogger.BeginTextColour((55, 55, 55))
					self.summaryLogger.BeginBold()
					self.summaryLogger.WriteText(item['key'])
					self.summaryLogger.EndBold()
					if not item['active']:
						self.summaryLogger.BeginTextColour((130, 0, 0))
						self.summaryLogger.WriteText(' '+_('[inactive]'))
						self.summaryLogger.BeginTextColour((55, 55, 55))
					else: self.summaryLogger.WriteText(' '+_('[active]'))
					self.summaryLogger.Newline()
					if 'zones' in item:
						for zone in item['zones']:
							if 'lower' in zone: lower = str(zone['lower'])
							else: lower = ''
							if 'upper' in zone: upper = str(zone['upper'])
							else: upper = ''
							if 'message' in zone: message = str(zone['message'])
							else: message = ''
							state = zone['state']
							if state == 'nominal': stateColour = visualNominal[0]
							if state == 'normal': stateColour = visualNormal[0]
							if state == 'alert': stateColour = visualAlert[0]
							if state == 'warn': stateColour = visualWarn[0]
							if state == 'alarm': stateColour = visualAlarm[0]
							if state == 'emergency': stateColour = visualEmergency[0]
							
							self.summaryLogger.BeginBold()
							self.summaryLogger.WriteText('    ↳')
							self.summaryLogger.EndBold()
							self.summaryLogger.BeginTextColour(stateColour)
							self.summaryLogger.BeginBold()
							self.summaryLogger.WriteText(state)
							self.summaryLogger.EndBold()
							self.summaryLogger.BeginTextColour((55, 55, 55))
							self.summaryLogger.WriteText(' ['+lower+'-'+upper+']')
							if zone['method']:
								self.summaryLogger.WriteText(' ['+', '.join(zone['method'])+']')
							if message: self.summaryLogger.WriteText(' ['+message+']')
							self.summaryLogger.Newline()
		else:
			self.summaryLogger.BeginTextColour((55, 55, 55)) 
			self.summaryLogger.WriteText(_('No zones found'))
			
	############################################################################

	def pageVisual(self):
		nominalLabel = wx.StaticText(self.visualMethod, label='nominal')
		self.visualNominal = wx.ColourPickerCtrl(self.visualMethod)
		self.nominalAuto = wx.CheckBox(self.visualMethod, label=_('auto closing'))

		normalLabel = wx.StaticText(self.visualMethod, label='normal')
		self.visualNormal = wx.ColourPickerCtrl(self.visualMethod)
		self.normalAuto = wx.CheckBox(self.visualMethod, label=_('auto closing'))

		alertLabel = wx.StaticText(self.visualMethod, label='alert')
		self.visualAlert = wx.ColourPickerCtrl(self.visualMethod)
		self.alertAuto = wx.CheckBox(self.visualMethod, label=_('auto closing'))

		warnLabel = wx.StaticText(self.visualMethod, label='warn')
		self.visualWarn = wx.ColourPickerCtrl(self.visualMethod)
		self.warnAuto = wx.CheckBox(self.visualMethod, label=_('auto closing'))

		alarmLabel = wx.StaticText(self.visualMethod, label='alarm')
		self.visualAlarm = wx.ColourPickerCtrl(self.visualMethod)
		self.alarmAuto = wx.CheckBox(self.visualMethod, label=_('auto closing'))

		emergencyLabel = wx.StaticText(self.visualMethod, label='emergency')
		self.visualEmergency= wx.ColourPickerCtrl(self.visualMethod)
		self.emergencyAuto = wx.CheckBox(self.visualMethod, label=_('auto closing'))

		self.toolbar2 = wx.ToolBar(self.visualMethod, style= wx.TB_VERTICAL)
		self.toolbar2.AddSeparator()
		save2 = self.toolbar2.AddTool(201, _('Save'), wx.Bitmap(self.currentdir+"/data/apply.png"))
		self.Bind(wx.EVT_TOOL, self.onSave2, save2)
		cancel2 = self.toolbar2.AddTool(202, _('Cancel'), wx.Bitmap(self.currentdir+"/data/cancel.png"))
		self.Bind(wx.EVT_TOOL, self.onCancel2, cancel2)
		self.toolbar2.AddSeparator()
		stopvisual = self.toolbar2.AddTool(203, _('Close all windows'), wx.Bitmap(self.currentdir+"/data/stop.png"))
		self.Bind(wx.EVT_TOOL, self.onStopAllVisual, stopvisual)
		self.toolbar2.AddSeparator()

		names = wx.BoxSizer(wx.VERTICAL)
		names.AddSpacer(5)
		names.Add(nominalLabel, 0, wx.ALL | wx.EXPAND, 10)
		names.Add(normalLabel, 0, wx.ALL | wx.EXPAND, 10)
		names.Add(alertLabel, 0, wx.ALL | wx.EXPAND, 10)
		names.Add(warnLabel, 0, wx.ALL | wx.EXPAND, 10)
		names.Add(alarmLabel, 0, wx.ALL | wx.EXPAND, 10)
		names.Add(emergencyLabel, 0, wx.ALL | wx.EXPAND, 10)

		colours = wx.BoxSizer(wx.VERTICAL)
		colours.AddSpacer(5)
		colours.Add(self.visualNominal, 0, wx.ALL | wx.EXPAND, 5)
		colours.Add(self.visualNormal, 0, wx.ALL | wx.EXPAND, 5)
		colours.Add(self.visualAlert, 0, wx.ALL | wx.EXPAND, 5)
		colours.Add(self.visualWarn, 0, wx.ALL | wx.EXPAND, 5)
		colours.Add(self.visualAlarm, 0, wx.ALL | wx.EXPAND, 5)
		colours.Add(self.visualEmergency, 0, wx.ALL | wx.EXPAND, 5)

		auto = wx.BoxSizer(wx.VERTICAL)
		auto.AddSpacer(5)
		auto.Add(self.nominalAuto, 0, wx.ALL | wx.EXPAND, 10)
		auto.Add(self.normalAuto, 0, wx.ALL | wx.EXPAND, 10)
		auto.Add(self.alertAuto, 0, wx.ALL | wx.EXPAND, 10)
		auto.Add(self.warnAuto, 0, wx.ALL | wx.EXPAND, 10)
		auto.Add(self.alarmAuto, 0, wx.ALL | wx.EXPAND, 10)
		auto.Add(self.emergencyAuto, 0, wx.ALL | wx.EXPAND, 10)

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(names, 0, wx.ALL | wx.EXPAND, 10)
		sizer.Add(colours, 1, wx.ALL | wx.EXPAND, 10)
		sizer.Add(auto, 0, wx.ALL | wx.EXPAND, 10)
		sizer.Add(self.toolbar2, 0,  wx.EXPAND, 0)
		self.visualMethod.SetSizer(sizer)

	def readColours(self):
		try: visualNominal = eval(self.conf.get('NOTIFICATIONS', 'visualNominal'))
		except: 
			visualNominal = [(0, 181, 30, 255), True]
			self.conf.set('NOTIFICATIONS', 'visualNominal', str(visualNominal))
		try: 
			self.visualNominal.SetColour(visualNominal[0])
			self.nominalAuto.SetValue(visualNominal[1])
		except: pass

		try: visualNormal = eval(self.conf.get('NOTIFICATIONS', 'visualNormal'))
		except: 
			visualNormal = [(46, 52, 54, 255), True]
			self.conf.set('NOTIFICATIONS', 'visualNormal', str(visualNormal))
		try: 
			self.visualNormal.SetColour(visualNormal[0])
			self.normalAuto.SetValue(visualNormal[1])
		except: pass

		try: visualAlert = eval(self.conf.get('NOTIFICATIONS', 'visualAlert'))
		except: 
			visualAlert = [(32, 74, 135, 255), True]
			self.conf.set('NOTIFICATIONS', 'visualAlert', str(visualAlert))
		try: 
			self.visualAlert.SetColour(visualAlert[0])
			self.alertAuto.SetValue(visualAlert[1])
		except: pass

		try: visualWarn = eval(self.conf.get('NOTIFICATIONS', 'visualWarn'))
		except: 
			visualWarn = [(196, 160, 0, 255), True]
			self.conf.set('NOTIFICATIONS', 'visualWarn', str(visualWarn))
		try: 
			self.visualWarn.SetColour(visualWarn[0])
			self.warnAuto.SetValue(visualWarn[1])
		except: pass

		try: visualAlarm = eval(self.conf.get('NOTIFICATIONS', 'visualAlarm'))
		except: 
			visualAlarm = [(206, 92, 0, 255), False]
			self.conf.set('NOTIFICATIONS', 'visualAlarm', str(visualAlarm))
		try: 
			self.visualAlarm.SetColour(visualAlarm[0])
			self.alarmAuto.SetValue(visualAlarm[1])
		except: pass

		try: visualEmergency = eval(self.conf.get('NOTIFICATIONS', 'visualEmergency'))
		except: 
			visualEmergency = [(164, 0, 0, 255), False]
			self.conf.set('NOTIFICATIONS', 'visualEmergency', str(visualEmergency))
		try: 
			self.visualEmergency.SetColour(visualEmergency[0])
			self.emergencyAuto.SetValue(visualEmergency[1])
		except: pass

	def onStopAllVisual(self,e):
		subprocess.call(['pkill','-f','openplotter-notifications-visual'])

	def onSave2(self,e):
		self.conf.set('NOTIFICATIONS', 'visualNominal', str([self.visualNominal.GetColour(),self.nominalAuto.GetValue()]))
		self.conf.set('NOTIFICATIONS', 'visualNormal', str([self.visualNormal.GetColour(),self.normalAuto.GetValue()]))
		self.conf.set('NOTIFICATIONS', 'visualAlert', str([self.visualAlert.GetColour(),self.alertAuto.GetValue()]))
		self.conf.set('NOTIFICATIONS', 'visualWarn', str([self.visualWarn.GetColour(),self.warnAuto.GetValue()]))
		self.conf.set('NOTIFICATIONS', 'visualAlarm', str([self.visualAlarm.GetColour(),self.alarmAuto.GetValue()]))
		self.conf.set('NOTIFICATIONS', 'visualEmergency', str([self.visualEmergency.GetColour(),self.emergencyAuto.GetValue()]))
		self.ShowStatusBarGREEN(_('Colours saved'))

	def onCancel2(self,e):
		self.readColours()
		self.ShowStatusBarRED(_('Colours reloaded'))

	############################################################################

	def pageSound(self):

		playButtonImg = wx.Bitmap(self.currentdir+"/data/play.png", wx.BITMAP_TYPE_ANY)

		nominalLabel = wx.StaticText(self.soundMethod, label='nominal')
		self.soundNominal = wx.TextCtrl(self.soundMethod)
		playButton0 = wx.BitmapButton(self.soundMethod, id=6000, bitmap=playButtonImg, size=(playButtonImg.GetWidth()+15, playButtonImg.GetHeight()+3))
		playButton0.Bind(wx.EVT_BUTTON, self.onPlayButton)
		nominalSelect = wx.Button(self.soundMethod, id=5000, label=_('Select'))
		nominalSelect.Bind(wx.EVT_BUTTON, self.OnFile)
		self.nominalStop = wx.CheckBox(self.soundMethod, label=_('auto stop'))

		normalLabel = wx.StaticText(self.soundMethod, label='normal')
		self.soundNormal = wx.TextCtrl(self.soundMethod)
		playButton1 = wx.BitmapButton(self.soundMethod, id=6001, bitmap=playButtonImg, size=(playButtonImg.GetWidth()+15, playButtonImg.GetHeight()+3))
		playButton1.Bind(wx.EVT_BUTTON, self.onPlayButton)
		normalSelect = wx.Button(self.soundMethod, id=5001, label=_('Select'))
		normalSelect.Bind(wx.EVT_BUTTON, self.OnFile)
		self.normalStop = wx.CheckBox(self.soundMethod, label=_('auto stop'))

		alertLabel = wx.StaticText(self.soundMethod, label='alert')
		self.soundAlert = wx.TextCtrl(self.soundMethod)
		playButton2 = wx.BitmapButton(self.soundMethod, id=6002, bitmap=playButtonImg, size=(playButtonImg.GetWidth()+15, playButtonImg.GetHeight()+3))
		playButton2.Bind(wx.EVT_BUTTON, self.onPlayButton)
		alertSelect = wx.Button(self.soundMethod, id=5002, label=_('Select'))
		alertSelect.Bind(wx.EVT_BUTTON, self.OnFile)
		self.alertStop = wx.CheckBox(self.soundMethod, label=_('auto stop'))

		warnLabel = wx.StaticText(self.soundMethod, label='warn')
		self.soundWarn = wx.TextCtrl(self.soundMethod)
		playButton3 = wx.BitmapButton(self.soundMethod, id=6003, bitmap=playButtonImg, size=(playButtonImg.GetWidth()+15, playButtonImg.GetHeight()+3))
		playButton3.Bind(wx.EVT_BUTTON, self.onPlayButton)
		warnSelect = wx.Button(self.soundMethod, id=5003, label=_('Select'))
		warnSelect.Bind(wx.EVT_BUTTON, self.OnFile)
		self.warnStop = wx.CheckBox(self.soundMethod, label=_('auto stop'))

		alarmLabel = wx.StaticText(self.soundMethod, label='alarm')
		self.soundAlarm = wx.TextCtrl(self.soundMethod)
		playButton4 = wx.BitmapButton(self.soundMethod, id=6004, bitmap=playButtonImg, size=(playButtonImg.GetWidth()+15, playButtonImg.GetHeight()+3))
		playButton4.Bind(wx.EVT_BUTTON, self.onPlayButton)
		alarmSelect = wx.Button(self.soundMethod, id=5004, label=_('Select'))
		alarmSelect.Bind(wx.EVT_BUTTON, self.OnFile)
		self.alarmStop = wx.CheckBox(self.soundMethod, label=_('auto stop'))

		emergencyLabel = wx.StaticText(self.soundMethod, label='emergency')
		self.soundEmergency= wx.TextCtrl(self.soundMethod)
		playButton5 = wx.BitmapButton(self.soundMethod, id=6005, bitmap=playButtonImg, size=(playButtonImg.GetWidth()+15, playButtonImg.GetHeight()+3))
		playButton5.Bind(wx.EVT_BUTTON, self.onPlayButton)
		emergencySelect = wx.Button(self.soundMethod, id=5005, label=_('Select'))
		emergencySelect.Bind(wx.EVT_BUTTON, self.OnFile)
		self.emergencyStop = wx.CheckBox(self.soundMethod, label=_('auto stop'))

		self.toolbar5 = wx.ToolBar(self.soundMethod, style= wx.TB_VERTICAL)
		self.toolbar5.AddSeparator()
		save2 = self.toolbar5.AddTool(501, _('Save'), wx.Bitmap(self.currentdir+"/data/apply.png"))
		self.Bind(wx.EVT_TOOL, self.onSave3, save2)
		cancel2 = self.toolbar5.AddTool(502, _('Cancel'), wx.Bitmap(self.currentdir+"/data/cancel.png"))
		self.Bind(wx.EVT_TOOL, self.onCancel3, cancel2)
		self.toolbar5.AddSeparator()
		stopsounds = self.toolbar5.AddTool(503, _('Stop all sounds'), wx.Bitmap(self.currentdir+"/data/sound-stop.png"))
		self.Bind(wx.EVT_TOOL, self.onStopAllSounds, stopsounds)
		self.toolbar5.AddSeparator()

		names = wx.BoxSizer(wx.VERTICAL)
		names.AddSpacer(10)
		names.Add(nominalLabel, 0, wx.ALL | wx.EXPAND, 11)
		names.Add(normalLabel, 0, wx.ALL | wx.EXPAND, 11)
		names.Add(alertLabel, 0, wx.ALL | wx.EXPAND, 11)
		names.Add(warnLabel, 0, wx.ALL | wx.EXPAND, 11)
		names.Add(alarmLabel, 0, wx.ALL | wx.EXPAND, 11)
		names.Add(emergencyLabel, 0, wx.ALL | wx.EXPAND, 11)

		nominal = wx.BoxSizer(wx.HORIZONTAL)
		nominal.Add(self.soundNominal, 1, wx.ALL | wx.EXPAND, 5)
		nominal.Add(playButton0, 0, wx.ALL | wx.EXPAND, 5)
		nominal.Add(nominalSelect, 0, wx.ALL | wx.EXPAND, 5)
		nominal.Add(self.nominalStop, 0, wx.ALL | wx.EXPAND, 5)

		normal = wx.BoxSizer(wx.HORIZONTAL)
		normal.Add(self.soundNormal, 1, wx.ALL | wx.EXPAND, 5)
		normal.Add(playButton1, 0, wx.ALL | wx.EXPAND, 5)
		normal.Add(normalSelect, 0, wx.ALL | wx.EXPAND, 5)
		normal.Add(self.normalStop, 0, wx.ALL | wx.EXPAND, 5)

		alert = wx.BoxSizer(wx.HORIZONTAL)
		alert.Add(self.soundAlert, 1, wx.ALL | wx.EXPAND, 5)
		alert.Add(playButton2, 0, wx.ALL | wx.EXPAND, 5)
		alert.Add(alertSelect, 0, wx.ALL | wx.EXPAND, 5)
		alert.Add(self.alertStop, 0, wx.ALL | wx.EXPAND, 5)

		warn = wx.BoxSizer(wx.HORIZONTAL)
		warn.Add(self.soundWarn, 1, wx.ALL | wx.EXPAND, 5)
		warn.Add(playButton3, 0, wx.ALL | wx.EXPAND, 5)
		warn.Add(warnSelect, 0, wx.ALL | wx.EXPAND, 5)
		warn.Add(self.warnStop, 0, wx.ALL | wx.EXPAND, 5)

		alarm = wx.BoxSizer(wx.HORIZONTAL)
		alarm.Add(self.soundAlarm, 1, wx.ALL | wx.EXPAND, 5)
		alarm.Add(playButton4, 0, wx.ALL | wx.EXPAND, 5)
		alarm.Add(alarmSelect, 0, wx.ALL | wx.EXPAND, 5)
		alarm.Add(self.alarmStop, 0, wx.ALL | wx.EXPAND, 5)

		emergency = wx.BoxSizer(wx.HORIZONTAL)
		emergency.Add(self.soundEmergency, 1, wx.ALL | wx.EXPAND, 5)
		emergency.Add(playButton5, 0, wx.ALL | wx.EXPAND, 5)
		emergency.Add(emergencySelect, 0, wx.ALL | wx.EXPAND, 5)
		emergency.Add(self.emergencyStop, 0, wx.ALL | wx.EXPAND, 5)

		sounds = wx.BoxSizer(wx.VERTICAL)
		sounds.AddSpacer(5)
		sounds.Add(nominal, 0, wx.EXPAND, 0)
		sounds.AddSpacer(5)
		sounds.Add(normal, 0, wx.EXPAND, 0)
		sounds.AddSpacer(5)
		sounds.Add(alert, 0, wx.EXPAND, 0)
		sounds.AddSpacer(5)
		sounds.Add(warn, 0, wx.EXPAND, 0)
		sounds.AddSpacer(5)
		sounds.Add(alarm, 0, wx.EXPAND, 0)
		sounds.AddSpacer(5)
		sounds.Add(emergency, 0, wx.EXPAND, 0)

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(names, 0, wx.ALL | wx.EXPAND, 10)
		sizer.Add(sounds, 1, wx.ALL | wx.EXPAND, 10)
		sizer.Add(self.toolbar5, 0,  wx.EXPAND, 0)
		self.soundMethod.SetSizer(sizer)

	def readSounds(self):
		try: soundNominal = eval(self.conf.get('NOTIFICATIONS', 'soundNominal'))
		except: 
			soundNominal = ['/usr/share/sounds/openplotter/bip.mp3', True]
			self.conf.set('NOTIFICATIONS', 'soundNominal', str(soundNominal))
		try: 
			self.soundNominal.SetValue(soundNominal[0])
			self.nominalStop.SetValue(soundNominal[1])
		except: pass

		try: soundNormal = eval(self.conf.get('NOTIFICATIONS', 'soundNormal'))
		except: 
			soundNormal = ['/usr/share/sounds/openplotter/Bleep.mp3', True]
			self.conf.set('NOTIFICATIONS', 'soundNormal', str(soundNormal))
		try: 
			self.soundNormal.SetValue(soundNormal[0])
			self.normalStop.SetValue(soundNormal[1])
		except: pass

		try: soundAlert = eval(self.conf.get('NOTIFICATIONS', 'soundAlert'))
		except: 
			soundAlert = ['/usr/share/sounds/openplotter/Store_Door_Chime.mp3', True]
			self.conf.set('NOTIFICATIONS', 'soundAlert', str(soundAlert))
		try: 
			self.soundAlert.SetValue(soundAlert[0])
			self.alertStop.SetValue(soundAlert[1])
		except: pass

		try: soundWarn = eval(self.conf.get('NOTIFICATIONS', 'soundWarn'))
		except: 
			soundWarn = ['/usr/share/sounds/openplotter/Ship_Bell.mp3', True]
			self.conf.set('NOTIFICATIONS', 'soundWarn', str(soundWarn))
		try: 
			self.soundWarn.SetValue(soundWarn[0])
			self.warnStop.SetValue(soundWarn[1])
		except: pass

		try: soundAlarm = eval(self.conf.get('NOTIFICATIONS', 'soundAlarm'))
		except: 
			soundAlarm = ['/usr/share/sounds/openplotter/pup-alert.mp3', False]
			self.conf.set('NOTIFICATIONS', 'soundAlarm', str(soundAlarm))
		try: 
			self.soundAlarm.SetValue(soundAlarm[0])
			self.alarmStop.SetValue(soundAlarm[1])
		except: pass

		try: soundEmergency = eval(self.conf.get('NOTIFICATIONS', 'soundEmergency'))
		except: 
			soundEmergency = ['/usr/share/sounds/openplotter/nuclear-alarm.ogg', False]
			self.conf.set('NOTIFICATIONS', 'soundEmergency', str(soundEmergency))
		try: 
			self.soundEmergency.SetValue(soundEmergency[0])
			self.emergencyStop.SetValue(soundEmergency[1])
		except: pass

	def onPlayButton(self,e):
		select = e.GetId()
		try:
			subprocess.call(['pkill','-15','vlc'])
			if select == 6000: subprocess.Popen(['cvlc', '--play-and-exit', self.soundNominal.GetValue()])
			elif select == 6001: subprocess.Popen(['cvlc', '--play-and-exit', self.soundNormal.GetValue()])
			elif select == 6002: subprocess.Popen(['cvlc', '--play-and-exit', self.soundAlert.GetValue()])
			elif select == 6003: subprocess.Popen(['cvlc', '--play-and-exit', self.soundWarn.GetValue()])
			elif select == 6004: subprocess.Popen(['cvlc', '--play-and-exit', self.soundAlarm.GetValue()])
			elif select == 6005: subprocess.Popen(['cvlc', '--play-and-exit', self.soundEmergency.GetValue()])
		except: self.ShowStatusBarRED(_('Failed: Error playing file'))

	def onStopAllSounds(self,e):
		subprocess.call(['pkill','-f','openplotter-notifications-sound'])

	def OnFile(self,e):
		select = e.GetId()
		dlg = wx.FileDialog(self, message=_('Choose a file'), defaultDir='/usr/share/sounds/openplotter', defaultFile='',
							wildcard=_('Audio files') + ' (*.mp3)|*.mp3|' + _('All files') + ' (*.*)|*.*',
							style=wx.FD_OPEN | wx.FD_CHANGE_DIR)
		if dlg.ShowModal() == wx.ID_OK:
			if select == 5000: self.soundNominal.SetValue(dlg.GetPath())
			elif select == 5001: self.soundNormal.SetValue(dlg.GetPath())
			elif select == 5002: self.soundAlert.SetValue(dlg.GetPath())
			elif select == 5003: self.soundWarn.SetValue(dlg.GetPath())
			elif select == 5004: self.soundAlarm.SetValue(dlg.GetPath())
			elif select == 5005: self.soundEmergency.SetValue(dlg.GetPath())
		dlg.Destroy()

	def onSave3(self,e):
		self.conf.set('NOTIFICATIONS', 'soundNominal', str([self.soundNominal.GetValue(), self.nominalStop.GetValue()]))
		self.conf.set('NOTIFICATIONS', 'soundNormal', str([self.soundNormal.GetValue(), self.normalStop.GetValue()]))
		self.conf.set('NOTIFICATIONS', 'soundAlert', str([self.soundAlert.GetValue(), self.alertStop.GetValue()]))
		self.conf.set('NOTIFICATIONS', 'soundWarn', str([self.soundWarn.GetValue(), self.warnStop.GetValue()]))
		self.conf.set('NOTIFICATIONS', 'soundAlarm', str([self.soundAlarm.GetValue(), self.alarmStop.GetValue()]))
		self.conf.set('NOTIFICATIONS', 'soundEmergency', str([self.soundEmergency.GetValue(), self.emergencyStop.GetValue()]))
		self.ShowStatusBarGREEN(_('Sounds saved'))

	def onCancel3(self,e):
		self.readSounds()
		self.ShowStatusBarRED(_('Sounds reloaded'))

	############################################################################

	def pageActions(self):

		self.key = wx.ComboBox(self.actions, 705, _('Notifications'), choices=[], style=wx.CB_DROPDOWN | wx.CB_READONLY)
		self.Bind(wx.EVT_COMBOBOX, self.onKey, self.key)

		self.listActions = wx.ListCtrl(self.actions, 152, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
		self.listActions.InsertColumn(0, _('Enabled'), width=70)
		self.listActions.InsertColumn(1, _('State'), width=90)
		self.listActions.InsertColumn(2, _('Message'), width=180)
		self.listActions.InsertColumn(3, _('Action'), width=180)
		self.listActions.InsertColumn(4, _('Data'), width=100)
		self.listActions.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onListActionsSelected)
		self.listActions.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onListActionsDeselected)
		self.listActions.EnableCheckBoxes(True)
		self.listActions.Bind(wx.EVT_LIST_ITEM_CHECKED, self.OnCheckItem)
		self.listActions.Bind(wx.EVT_LIST_ITEM_UNCHECKED, self.OnUnCheckItem)

		self.checking = False
		self.listActions.SetTextColour(wx.BLACK)

		self.toolbar7 = wx.ToolBar(self.actions, style=wx.TB_VERTICAL)
		self.toolbar7.AddSeparator()
		addAction = self.toolbar7.AddTool(705, _('Add'), wx.Bitmap(self.currentdir+"/data/add.png"))
		self.Bind(wx.EVT_TOOL, self.onAddAction, addAction)
		self.toolbar7.AddSeparator()
		toolEdit = self.toolbar7.AddTool(701, _('Edit'), wx.Bitmap(self.currentdir+"/data/edit.png"))
		self.Bind(wx.EVT_TOOL, self.onEditAction, toolEdit)
		toolDelete = self.toolbar7.AddTool(702, _('Delete'), wx.Bitmap(self.currentdir+"/data/cancel.png"))
		self.Bind(wx.EVT_TOOL, self.onDeleteAction, toolDelete)
		self.toolbar7.AddSeparator()
		toolUp = self.toolbar7.AddTool(703, _('Up'), wx.Bitmap(self.currentdir+"/data/up.png"))
		self.Bind(wx.EVT_TOOL, self.onToolUp, toolUp)
		toolDown = self.toolbar7.AddTool(704, _('Down'), wx.Bitmap(self.currentdir+"/data/down.png"))
		self.Bind(wx.EVT_TOOL, self.onToolDown, toolDown)
		self.toolbar7.AddSeparator()

		hbox1 = wx.BoxSizer(wx.HORIZONTAL)
		hbox1.Add(self.listActions , 1, wx.ALL | wx.EXPAND, 0)
		hbox1.Add(self.toolbar7 , 0, wx.EXPAND, 0)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(self.key, 0, wx.ALL |  wx.EXPAND, 10)
		vbox.Add(hbox1, 1, wx.EXPAND, 0)
		self.actions.SetSizer(vbox)

	def readNotifications(self):
		self.keysList = []
		try: self.actionsList0 = eval(self.conf.get('NOTIFICATIONS', 'actions'))
		except: self.actionsList0 = {}
		for i in self.actionsList0:
			self.keysList.append(i)
		self.key.Clear()
		self.listActions.DeleteAllItems()
		self.onListActionsDeselected()
		self.key.AppendItems(self.keysList)
		self.key.SetSelection(0)
		key = self.key.GetValue()
		self.readSelectedActions(key)

	def onKey(self,e=0):
		selected = self.key.GetSelection()
		if selected != -1:
			keySelected = self.key.GetValue()
			self.readSelectedActions(keySelected)

	def readSelectedActions(self,keySelected):
		if keySelected:
			if keySelected in self.actionsList0:
				self.actionsSelected = self.actionsList0[keySelected]
				self.listActions.DeleteAllItems()
				self.onListActionsDeselected()
				self.checking = False
				for i in self.actionsSelected:
					index = self.listActions.InsertItem(sys.maxsize, '')
					self.listActions.SetItem(index, 1, i['state'])
					self.listActions.SetItem(index, 2, i['message'])
					self.listActions.SetItem(index, 3, i['name'])
					self.listActions.SetItem(index, 4, i['data'])
					if i['enabled']: self.listActions.CheckItem(index)
				self.checking = True

	def onListActionsSelected(self, e):
		selected = self.listActions.GetFirstSelected()
		if selected == -1: return
		self.toolbar7.EnableTool(701,True)
		self.toolbar7.EnableTool(702,True)
		if selected == 0: self.toolbar7.EnableTool(703,False)
		else: self.toolbar7.EnableTool(703,True)
		c = self.listActions.GetItemCount()
		if selected == c-1: self.toolbar7.EnableTool(704,False)
		else: self.toolbar7.EnableTool(704,True)

	def onListActionsDeselected(self, event=0):
		self.toolbar7.EnableTool(701,False)
		self.toolbar7.EnableTool(702,False)
		self.toolbar7.EnableTool(703,False)
		self.toolbar7.EnableTool(704,False)

	def OnCheckItem(self, index):
		if self.checking:
			i = index.GetIndex()
			key = self.key.GetValue()
			self.actionsList0[key][i]['enabled'] = True
			self.conf.set('NOTIFICATIONS', 'actions', str(self.actionsList0))
			self.readSelectedActions(key)
			self.restartRead()

	def OnUnCheckItem(self, index):
		if self.checking:
			i = index.GetIndex()
			key = self.key.GetValue()
			self.actionsList0[key][i]['enabled'] = False
			self.conf.set('NOTIFICATIONS', 'actions', str(self.actionsList0))
			self.readSelectedActions(key)
			self.restartRead()

	def onAddAction(self,e):
		edit = {}
		self.setAction(edit)

	def onToolUp(self,e):
		selected = self.listActions.GetFirstSelected()
		if selected == -1 or selected == 0: return
		key = self.key.GetValue()
		self.actionsList0[key][selected],self.actionsList0[key][selected-1] = self.actionsList0[key][selected-1],self.actionsList0[key][selected]
		self.conf.set('NOTIFICATIONS', 'actions', str(self.actionsList0))
		self.readSelectedActions(key)
		self.restartRead()

	def onToolDown(self,e):
		c = self.listActions.GetItemCount()
		selected = self.listActions.GetFirstSelected()
		if selected == -1 or selected == c-1: return
		key = self.key.GetValue()
		self.actionsList0[key][selected],self.actionsList0[key][selected+1] = self.actionsList0[key][selected+1],self.actionsList0[key][selected]
		self.conf.set('NOTIFICATIONS', 'actions', str(self.actionsList0))
		self.readSelectedActions(key)
		self.restartRead()

	def onEditAction(self,e):
		selected = self.listActions.GetFirstSelected()
		if selected == -1: return
		key = self.key.GetValue()
		state = self.actionsSelected[selected]['state']
		message = self.actionsSelected[selected]['message']
		module = self.actionsSelected[selected]['module']
		ID = self.actionsSelected[selected]['ID']
		data = self.actionsSelected[selected]['data']
		edit = {'key':key,'selected':selected,'state':state,'message':message,'module':module,'ID':ID,'data':data}
		self.setAction(edit)

	def setAction(self,edit):
		dlg = editAction(edit)
		res = dlg.ShowModal()
		if res == wx.ID_OK:
			key = dlg.keyResult
			action = dlg.actionResult
			if key in self.actionsList0:
				if not edit: self.actionsList0[key].append(action)
				else: self.actionsList0[key][edit['selected']] = action
			else: self.actionsList0[key] = [action]
			self.conf.set('NOTIFICATIONS', 'actions', str(self.actionsList0))
			self.readNotifications()
			self.key.SetValue(key)
			self.readSelectedActions(key)
		dlg.Destroy()
		self.restartRead()

	def onDeleteAction(self,e):
		selected = self.listActions.GetFirstSelected()
		if selected == -1: return
		key = self.key.GetValue()
		del self.actionsList0[key][selected]
		deleted = False
		if len(self.actionsList0[key]) == 0:
			deleted = True
			del self.actionsList0[key]
		self.conf.set('NOTIFICATIONS', 'actions', str(self.actionsList0))
		self.readNotifications()
		if not deleted:
			self.key.SetValue(key)
			self.readSelectedActions(key)
		self.restartRead()

################################################################################

class editAction(wx.Dialog):

	def __init__(self,edit):
		if edit: title = _('Editing Action')
		else: title = _('Adding Action')

		from openplotterSettings import appsList
		import importlib

		self.conf = conf.Conf()
		self.currentLanguage = self.conf.get('GENERAL', 'lang')
		if self.conf.get('GENERAL', 'debug') == 'yes': self.debug = True
		else: self.debug = False

		self.availableActions = []
		self.appsList = appsList.AppsList()
		appsDict = self.appsList.appsDict
		for i in appsDict:
			name = i['module']
			if name:
				actions = False
				try:
					actions = importlib.import_module(name+'.actions')
					if actions: 
						target = actions.Actions(self.conf,self.currentLanguage)
						available = target.available
						if available:
							for i in available:
								self.availableActions.append(i)
				except Exception as e: 
					if self.debug: print(str(e))

		self.actions = []
		for i in self.availableActions:
			self.actions.append(i['name'])

		wx.Dialog.__init__(self, None, title=title, size=(600, 425))
		self.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		panel = wx.Panel(self)

		stateLabel= wx.StaticText(panel, label = _('State'))
		self.state = wx.ComboBox(panel, choices = [_('any'),'null','nominal','normal','alert','warn','alarm','emergency'], style=wx.CB_READONLY)
		if edit:
			if edit['state'] == '': self.state.SetSelection(0)
			else: self.state.SetValue(edit['state'])
		else: self.state.SetSelection(0)
		self.Bind(wx.EVT_COMBOBOX, self.onState, self.state)

		messageLabel= wx.StaticText(panel, label = _('Message'))
		self.message = wx.TextCtrl(panel,size=(-1, 25))
		if edit: 
			if edit['state'] == 'null': self.message.Disable()
			else: self.message.SetValue(edit['message'])

		notiLabel = wx.StaticText(panel, label = _('Notification'))
		self.SK = wx.TextCtrl(panel,size=(-1, 25))
		SKedit = wx.Button(panel, label='Signal K key')
		SKedit.Bind(wx.EVT_BUTTON, self.onSKedit)
		if edit:
			self.SK.SetValue(edit['key'])
			self.SK.Disable()
			SKedit.Disable()

		actionLabel= wx.StaticText(panel, label = _('Action'))
		self.actionsList = wx.ComboBox(panel, choices = self.actions, style=wx.CB_READONLY)
		self.Bind(wx.EVT_COMBOBOX, self.onActionsList, self.actionsList)

		dataLabel= wx.StaticText(panel, label = _('Data'))
		self.data = wx.TextCtrl(panel,style= wx.TE_MULTILINE)

		self.stateBtn = wx.Button(panel, label='< '+_('state'))
		self.stateBtn.Bind(wx.EVT_BUTTON, self.onAddState)
		self.messageBtn = wx.Button(panel, label='< '+_('message'))
		self.messageBtn.Bind(wx.EVT_BUTTON, self.onAddMessage)
		self.timestampBtn = wx.Button(panel, label='< '+_('timestamp'))
		self.timestampBtn.Bind(wx.EVT_BUTTON, self.onAddTimestamp)
		self.skBtn = wx.Button(panel, label='< '+_('Signal K value'))
		self.skBtn.Bind(wx.EVT_BUTTON, self.onAddsk)

		self.help= wx.StaticText(panel, label = '')

		self.data.Disable()
		self.stateBtn.Disable()
		self.messageBtn.Disable()
		self.timestampBtn.Disable()
		self.skBtn.Disable()
		self.help.SetLabel('')

		if edit: 
			for i in self.availableActions:
				if i['module'] == edit['module']:
					if i['ID'] == edit['ID']:
						self.actionsList.SetValue(i['name'])
						if i['data']:
							self.data.Enable()
							self.stateBtn.Enable()
							self.messageBtn.Enable()
							self.timestampBtn.Enable()
							self.skBtn.Enable()
							self.data.SetValue(edit['data'])
							self.help.SetLabel(i['help'])		

		cancelBtn = wx.Button(panel, wx.ID_CANCEL)
		okBtn = wx.Button(panel, wx.ID_OK)
		okBtn.Bind(wx.EVT_BUTTON, self.ok)

		v1 = wx.BoxSizer(wx.VERTICAL)
		v1.Add(stateLabel, 0, wx.ALL | wx.EXPAND, 3)
		v1.Add(self.state, 0, wx.ALL | wx.EXPAND, 3)

		v2 = wx.BoxSizer(wx.VERTICAL)
		v2.Add(messageLabel, 0, wx.ALL | wx.EXPAND, 3)
		v2.Add(self.message, 0, wx.ALL | wx.EXPAND, 3)

		h1 = wx.BoxSizer(wx.HORIZONTAL)
		h1.Add(v1, 0, wx.ALL | wx.EXPAND, 0)
		h1.Add(v2, 1, wx.ALL | wx.EXPAND, 0)

		h3 = wx.BoxSizer(wx.HORIZONTAL)
		h3.Add(self.SK, 1, wx.ALL, 3)
		h3.Add(SKedit, 0, wx.ALL, 3)

		v3 = wx.BoxSizer(wx.VERTICAL)
		v3.Add(self.stateBtn, 0, wx.ALL | wx.EXPAND, 3)
		v3.Add(self.messageBtn, 0, wx.ALL | wx.EXPAND, 3)
		v3.Add(self.timestampBtn, 0, wx.ALL | wx.EXPAND, 3)
		v3.Add(self.skBtn, 0, wx.ALL | wx.EXPAND, 3)

		h4 = wx.BoxSizer(wx.HORIZONTAL)
		h4.Add(self.data, 1, wx.ALL  | wx.EXPAND, 3)
		h4.Add(v3, 0, wx.ALL | wx.EXPAND, 0)

		actionbox = wx.BoxSizer(wx.HORIZONTAL)
		actionbox.AddStretchSpacer(1)
		actionbox.Add(cancelBtn, 0, wx.LEFT | wx.EXPAND, 10)
		actionbox.Add(okBtn, 0, wx.LEFT | wx.EXPAND, 10)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(notiLabel, 0, wx.ALL  | wx.EXPAND, 3)
		vbox.Add(h3, 0, wx.ALL | wx.EXPAND, 0)
		vbox.Add(h1, 0, wx.ALL | wx.EXPAND, 0)
		vbox.Add(actionLabel, 0, wx.ALL  | wx.EXPAND, 3)
		vbox.Add(self.actionsList , 0, wx.ALL  | wx.EXPAND, 3)
		vbox.Add(dataLabel, 0, wx.ALL  | wx.EXPAND, 3)
		vbox.Add(h4, 1, wx.ALL | wx.EXPAND, 0)
		vbox.Add(self.help, 0, wx.LEFT | wx.EXPAND, 3)
		vbox.Add(actionbox, 0, wx.ALL | wx.EXPAND, 10)

		panel.SetSizer(vbox)
		self.panel = panel

		self.Centre() 

	def onActionsList(self,e=0):
		selected = self.actionsList.GetSelection()
		if selected != -1:
			if self.availableActions[selected]['data']:
				self.data.Enable()
				self.stateBtn.Enable()
				self.messageBtn.Enable()
				self.timestampBtn.Enable()
				self.skBtn.Enable()
				self.data.SetValue(self.availableActions[selected]['default'])
				self.help.SetLabel(self.availableActions[selected]['help'])
			else: 
				self.data.SetValue('')
				self.data.Disable()
				self.stateBtn.Disable()
				self.messageBtn.Disable()
				self.timestampBtn.Disable()
				self.skBtn.Disable()
				self.help.SetLabel('')

	def onState(self,e=0):
		selected = self.state.GetSelection()
		if selected == 1: 
			self.message.Disable()
			self.message.SetValue('')
		else: self.message.Enable()

	def onSKedit(self,e):
		dlg = selectKey.SelectKey(self.SK.GetValue(),1)
		res = dlg.ShowModal()
		if res == wx.OK:
			key = dlg.selected_key.replace(':','.')
			if not 'notifications.' in key: key = 'notifications.'+key
			vessel = dlg.skvessels.GetValue()
			self.SK.SetValue(vessel+'.'+key)
		dlg.Destroy()

	def onAddState(self,e):
		self.data.AppendText('<|s|>')

	def onAddMessage(self,e):
		self.data.AppendText('<|m|>')

	def onAddTimestamp(self,e):
		self.data.AppendText('<|t|>')

	def onAddsk(self,e):
		dlg = selectKey.SelectKey('',1)
		res = dlg.ShowModal()
		if res == wx.OK:
			key = dlg.selected_key.replace(':','.')
			vessel = dlg.skvessels.GetValue()
			self.data.AppendText('<|'+vessel+'||'+key+'|>')
		dlg.Destroy()

	def ok(self,e):
		self.keyResult = self.SK.GetValue()
		if not self.keyResult:
			wx.MessageBox(_('Notification failed: provide a notification key.'), _('Info'), wx.OK | wx.ICON_INFORMATION)
			return
		if not re.match('^[-:.0-9a-zA-Z]+$', self.keyResult):
			wx.MessageBox(_('Notification failed: characters not allowed.'), _('Info'), wx.OK | wx.ICON_INFORMATION)
			return
		items = self.keyResult.split('.')
		if items[0] == 'vessels': del items[0]
		if items[0] != 'self' and items[0][0:12] != 'urn:mrn:imo:' and items[0][0:16] != 'urn:mrn:signalk:': items.insert(0, 'self')
		if items[1] != 'notifications': items.insert(1, 'notifications')
		self.keyResult = '.'.join(items)
		if self.state.GetSelection() == 0: state = ''
		else: state = self.state.GetValue()
		message = self.message.GetValue()
		selected = self.actionsList.GetSelection()
		if selected == -1:
			wx.MessageBox(_('Action failed: select an action.'), _('Info'), wx.OK | wx.ICON_INFORMATION)
			return
		name = self.availableActions[selected]['name']
		module = self.availableActions[selected]['module']
		ID = self.availableActions[selected]['ID']
		name = self.availableActions[selected]['name']
		data = self.data.GetValue()
		self.actionResult = {'enabled': True,'state':state,'message':message,'name':name,'module':module,'ID':ID,'data':data}
		self.EndModal(wx.ID_OK)

################################################################################

class editCustom(wx.Dialog):

	def __init__(self,edit):
		if edit: title = _('Editing notification')
		else: title = _('Adding notification')

		self.conf = conf.Conf()
		self.currentLanguage = self.conf.get('GENERAL', 'lang')
		if self.conf.get('GENERAL', 'debug') == 'yes': self.debug = True
		else: self.debug = False

		wx.Dialog.__init__(self, None, title=title, size=(450, 320))
		self.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		panel = wx.Panel(self)

		stateLabel= wx.StaticText(panel, label = _('State'))
		self.state = wx.ComboBox(panel, choices = ['nominal','normal','alert','warn','alarm','emergency'], style=wx.CB_READONLY)
		if edit:
			if edit['state'] == '': self.state.SetSelection(0)
			else: self.state.SetValue(edit['state'])
		else: self.state.SetSelection(0)

		messageLabel= wx.StaticText(panel, label = _('Message'))
		self.message = wx.TextCtrl(panel)
		if edit: self.message.SetValue(edit['message'])

		notiLabel = wx.StaticText(panel, label = _('Notification'))
		self.SK = wx.TextCtrl(panel,size=(-1, 25))
		SKedit = wx.Button(panel, label='Signal K key')
		SKedit.Bind(wx.EVT_BUTTON, self.onSKedit)
		if edit: self.SK.SetValue(edit['key'])

		methodLabel = wx.StaticText(panel, label = _('Method'))
		self.visual = wx.CheckBox(panel, label='visual')
		self.sound = wx.CheckBox(panel, label='sound')
		if edit:
			if 'visual' in edit['method']: self.visual.SetValue(True)
			if 'sound' in edit['method']: self.sound.SetValue(True)

		cancelBtn = wx.Button(panel, wx.ID_CANCEL)
		okBtn = wx.Button(panel, wx.ID_OK)
		okBtn.Bind(wx.EVT_BUTTON, self.ok)

		v1 = wx.BoxSizer(wx.VERTICAL)
		v1.Add(stateLabel, 0, wx.ALL | wx.EXPAND, 5)
		v1.Add(self.state, 0, wx.ALL | wx.EXPAND, 5)

		v2 = wx.BoxSizer(wx.VERTICAL)
		v2.Add(messageLabel, 0, wx.ALL | wx.EXPAND, 5)
		v2.Add(self.message, 1, wx.ALL | wx.EXPAND, 5)

		h1 = wx.BoxSizer(wx.HORIZONTAL)
		h1.Add(v1, 0, wx.ALL | wx.EXPAND, 0)
		h1.Add(v2, 1, wx.ALL | wx.EXPAND, 0)

		h3 = wx.BoxSizer(wx.HORIZONTAL)
		h3.Add(self.SK, 1, wx.ALL, 5)
		h3.Add(SKedit, 0, wx.ALL, 5)

		h4 = wx.BoxSizer(wx.HORIZONTAL)
		h4.Add(self.visual, 0, wx.ALL, 5)
		h4.Add(self.sound, 0, wx.ALL, 5)

		actionbox = wx.BoxSizer(wx.HORIZONTAL)
		actionbox.AddStretchSpacer(1)
		actionbox.Add(cancelBtn, 0, wx.LEFT | wx.EXPAND, 10)
		actionbox.Add(okBtn, 0, wx.LEFT | wx.EXPAND, 10)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(notiLabel, 0, wx.ALL  | wx.EXPAND, 5)
		vbox.Add(h3, 0, wx.ALL | wx.EXPAND, 0)
		vbox.Add(h1, 0, wx.ALL | wx.EXPAND, 0)
		vbox.Add(methodLabel, 0, wx.ALL  | wx.EXPAND, 5)
		vbox.Add(h4, 0, wx.ALL, 0)
		vbox.AddStretchSpacer(1)
		vbox.Add(actionbox, 0, wx.ALL | wx.EXPAND, 10)

		panel.SetSizer(vbox)
		self.panel = panel

		self.Centre() 

	def onSKedit(self,e):
		dlg = selectKey.SelectKey(self.SK.GetValue(),0)
		res = dlg.ShowModal()
		if res == wx.OK:
			key = dlg.selected_key.replace(':','.')
			self.SK.SetValue(key)
		dlg.Destroy()

	def ok(self,e):
		self.keyResult = self.SK.GetValue()
		if not self.keyResult:
			wx.MessageBox(_('Notification failed: provide a notification key.'), _('Info'), wx.OK | wx.ICON_INFORMATION)
			return
		if not re.match('^[-:.0-9a-zA-Z]+$', self.keyResult):
			wx.MessageBox(_('Notification failed: characters not allowed.'), _('Info'), wx.OK | wx.ICON_INFORMATION)
			return
		if not 'notifications.' in self.keyResult: self.keyResult = 'notifications.'+self.keyResult 
		self.EndModal(wx.ID_OK)

################################################################################

def main():
	try:
		platform2 = platform.Platform()
		if not platform2.postInstall(version,'notifications'):
			subprocess.Popen(['openplotterPostInstall', 'notificationsPostInstall'])
			return
	except: pass

	app = wx.App()
	MyFrame().Show()
	time.sleep(1)
	app.MainLoop()

if __name__ == '__main__':
	main()
