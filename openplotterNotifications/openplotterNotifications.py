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

import wx, os, sys, webbrowser, subprocess, time, ujson
import wx.richtext as rt
from openplotterSettings import conf
from openplotterSettings import language
from openplotterSettings import platform
from openplotterSignalkInstaller import connections
from .version import version

class MyFrame(wx.Frame):
	def __init__(self):
		if not 'openplotter-notifications-read' in subprocess.check_output(['ps','aux']).decode(sys.stdin.encoding): subprocess.Popen('openplotter-notifications-read')
		self.conf = conf.Conf()
		self.conf_folder = self.conf.conf_folder
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
		aproveSK = self.toolbar1.AddTool(105, _('Approve'), wx.Bitmap(self.currentdir+"/data/sk.png"))
		self.Bind(wx.EVT_TOOL, self.onAproveSK, aproveSK)
		connectionSK = self.toolbar1.AddTool(106, _('Allowed'), wx.Bitmap(self.currentdir+"/data/sk.png"))
		self.Bind(wx.EVT_TOOL, self.onConnectionSK, connectionSK)
		self.toolbar1.AddSeparator()
		refresh = self.toolbar1.AddTool(104, _('Refresh'), wx.Bitmap(self.currentdir+"/data/refresh.png"))
		self.Bind(wx.EVT_TOOL, self.onRefresh, refresh)

		self.notebook = wx.Notebook(self)
		self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onTabChange)
		self.summary = wx.Panel(self.notebook)
		self.visualMethod = wx.Panel(self.notebook)
		self.soundMethod = wx.Panel(self.notebook)
		self.sk = wx.Panel(self.notebook)
		self.command = wx.Panel(self.notebook)
		self.gpio = wx.Panel(self.notebook)
		self.mqtt = wx.Panel(self.notebook)
		self.mastodon = wx.Panel(self.notebook)
		self.telegram = wx.Panel(self.notebook)
		self.sms = wx.Panel(self.notebook)
		self.email = wx.Panel(self.notebook)
		self.notebook.AddPage(self.summary, _('Thresholds'))
		self.notebook.AddPage(self.visualMethod, _('Visual'))
		self.notebook.AddPage(self.soundMethod, _('Sound'))
		self.notebook.AddPage(self.command, _('Command'))
		self.notebook.AddPage(self.sk, 'Signal K key')
		self.notebook.AddPage(self.gpio, 'GPIO')
		self.notebook.AddPage(self.mqtt, 'MQTT')
		self.notebook.AddPage(self.mastodon, 'Mastodon')
		self.notebook.AddPage(self.telegram, 'Telegram')
		self.notebook.AddPage(self.email, 'Email')
		self.notebook.AddPage(self.sms, 'SMS')
		self.il = wx.ImageList(24, 24)
		img0 = self.il.Add(wx.Bitmap(self.currentdir+"/data/sk.png", wx.BITMAP_TYPE_PNG))
		img1 = self.il.Add(wx.Bitmap(self.currentdir+"/data/visual.png", wx.BITMAP_TYPE_PNG))
		img2 = self.il.Add(wx.Bitmap(self.currentdir+"/data/play.png", wx.BITMAP_TYPE_PNG))
		self.notebook.AssignImageList(self.il)
		self.notebook.SetPageImage(0, img0)
		self.notebook.SetPageImage(1, img1)
		self.notebook.SetPageImage(2, img2)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(self.toolbar1, 0, wx.EXPAND)
		vbox.Add(self.notebook, 1, wx.EXPAND)
		self.SetSizer(vbox)

		self.pageSummary()
		self.pageVisual()
		self.pageSound()
		self.pageCommand()
		self.pageSK()
		
		self.onRefresh()

		maxi = self.conf.get('GENERAL', 'maximize')
		if maxi == '1': self.Maximize()

		self.Centre()


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
		url = "/usr/share/openplotter-doc/external/myapp_app.html"
		webbrowser.open(url, new=2)

	def OnToolSettings(self, event=0): 
		subprocess.call(['pkill', '-f', 'openplotter-settings'])
		subprocess.Popen('openplotter-settings')

	def onAproveSK(self,e):
		if self.platform.skPort: 
			url = self.platform.http+'localhost:'+self.platform.skPort+'/admin/#/security/access/requests'
			webbrowser.open(url, new=2)

	def onConnectionSK(self,e):
		if self.platform.skPort: 
			url = self.platform.http+'localhost:'+self.platform.skPort+'/admin/#/security/devices'
			webbrowser.open(url, new=2)

	def onRefresh(self, e=0):
		self.ShowStatusBarBLACK(' ')
		self.toolbar1.EnableTool(105,False)
		skConnections = connections.Connections('NOTIFICATIONS')
		result = skConnections.checkConnection()
		if result[0] == 'pending':
			self.toolbar1.EnableTool(105,True)
			self.ShowStatusBarYELLOW(result[1]+_(' Press "Approve" and then "Refresh".'))
		elif result[0] == 'error':
			self.ShowStatusBarRED(result[1])
		elif result[0] == 'repeat':
			self.ShowStatusBarYELLOW(result[1]+_(' Press "Refresh".'))
		elif result[0] == 'permissions':
			self.ShowStatusBarYELLOW(result[1]+_(' Press "Allowed".'))
		elif result[0] == 'approved':
			self.ShowStatusBarGREEN(result[1])

		self.OnReadThresholds()

	############################################################################

	def pageSummary(self):
		self.summaryLogger = rt.RichTextCtrl(self.summary, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_DONTWRAP|wx.LC_SORT_ASCENDING)
		self.summaryLogger.SetMargins((10,10))

		self.toolbar3 = wx.ToolBar(self.summary, style=wx.TB_TEXT | wx.TB_VERTICAL)
		toolThresholds = self.toolbar3.AddTool(301, _('Edit'), wx.Bitmap(self.currentdir+"/data/sk.png"))
		self.Bind(wx.EVT_TOOL, self.OnToolThresholds, toolThresholds)

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(self.summaryLogger, 1, wx.EXPAND, 0)
		sizer.Add(self.toolbar3, 0,  wx.EXPAND, 0)
		self.summary.SetSizer(sizer)

	def OnToolThresholds(self, e):
		if self.platform.skPort: 
			if self.platform.isSKpluginInstalled('signalk-threshold-notifier'):
				url = self.platform.http+'localhost:'+self.platform.skPort+'/admin/#/serverConfiguration/plugins/threshold-notifier'
			else: 
				self.ShowStatusBarRED(_('Please install "signalk-threshold-notifier" Signal K app'))
				url = self.platform.http+'localhost:'+self.platform.skPort+'/admin/#/appstore/apps'
			webbrowser.open(url, new=2)
		else: 
			self.ShowStatusBarRED(_('Please install "Signal K Installer" OpenPlotter app'))
			self.OnToolSettings()

	def OnReadThresholds(self):
		self.summaryLogger.Clear()
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
		file = self.platform.skDir+'/plugin-config-data/threshold-notifier.json'
		try:
			with open(file) as data_file:
				data = ujson.load(data_file)
				if not data['enabled']:
					self.summaryLogger.BeginTextColour((130, 0, 0)) 
					self.summaryLogger.WriteText(_('Failed: signalk-threshold-notifier is disabled'))
					return
		except:
			self.summaryLogger.BeginTextColour((130, 0, 0)) 
			self.summaryLogger.WriteText(_('Failed: error reading signalk-threshold-notifier plugin configuration. Is this Signal K plugin installed and enabled?'))
			return
		if 'paths' in data['configuration']:
			skKeys = {}
			for path in data['configuration']['paths']:
				if 'enabled' in path['options']:
					if not path['path'] in skKeys: skKeys[path['path']] = {}
					if 'value' in path['highthreshold']:
						if not path['highthreshold']['state'] in skKeys[path['path']]: skKeys[path['path']][path['highthreshold']['state']] = []
						skKeys[path['path']][path['highthreshold']['state']].append({'highthreshold':path['highthreshold'],'message':path['message']})
					if 'value' in path['lowthreshold']:
						if not path['lowthreshold']['state'] in skKeys[path['path']]: skKeys[path['path']][path['lowthreshold']['state']] = []
						skKeys[path['path']][path['lowthreshold']['state']].append({'lowthreshold':path['lowthreshold'],'message':path['message']})
				
			for path in skKeys:
				self.summaryLogger.BeginTextColour((55, 55, 55))
				self.summaryLogger.BeginBold()
				self.summaryLogger.WriteText(path)
				self.summaryLogger.EndBold()
				self.summaryLogger.EndTextColour()
				self.summaryLogger.Newline()
				for state in skKeys[path]:
					if state == 'normal': stateColour = visualNormal[0]
					if state == 'alert': stateColour = visualAlert[0]
					if state == 'warn': stateColour = visualWarn[0]
					if state == 'alarm': stateColour = visualAlarm[0]
					if state == 'emergency': stateColour = visualEmergency[0]
					self.summaryLogger.BeginTextColour(stateColour)
					self.summaryLogger.WriteText('      '+state)
					self.summaryLogger.EndTextColour()
					self.summaryLogger.Newline()
					self.summaryLogger.BeginTextColour((55, 55, 55))
					for i in skKeys[path][state]:
						if 'highthreshold' in i:
							self.summaryLogger.WriteText('            '+_('High threshold: ')+str(i['highthreshold']['value']))
							self.summaryLogger.Newline()
							if 'message' in i: 
								self.summaryLogger.WriteText('                  '+_('Message: ')+i['message'])
								self.summaryLogger.Newline()
							if i['highthreshold']['method']: 
								self.summaryLogger.WriteText('                  '+_('Methods: ')+', '.join(i['highthreshold']['method']))
								self.summaryLogger.Newline()
						if 'lowthreshold' in i:
							self.summaryLogger.WriteText('            '+_('Low threshold: ')+str(i['lowthreshold']['value']))
							self.summaryLogger.Newline()
							if 'message' in i: 
								self.summaryLogger.WriteText('                  '+_('Message: ')+i['message'])
								self.summaryLogger.Newline()
							if i['lowthreshold']['method']: 
								self.summaryLogger.WriteText('                  '+_('Methods: ')+', '.join(i['lowthreshold']['method']))
								self.summaryLogger.Newline()
				self.summaryLogger.EndTextColour()
		else:
			self.summaryLogger.BeginTextColour((55, 55, 55)) 
			self.summaryLogger.WriteText(_('No thresholds found'))
			
	############################################################################

	def pageVisual(self):
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

		self.toolbar2 = wx.ToolBar(self.visualMethod, style=wx.TB_TEXT | wx.TB_VERTICAL)
		save2 = self.toolbar2.AddTool(201, _('Save'), wx.Bitmap(self.currentdir+"/data/apply.png"))
		self.Bind(wx.EVT_TOOL, self.onSave2, save2)
		cancel2 = self.toolbar2.AddTool(202, _('Cancel'), wx.Bitmap(self.currentdir+"/data/cancel.png"))
		self.Bind(wx.EVT_TOOL, self.onCancel2, cancel2)
		self.toolbar2.AddSeparator()
		stopvisual = self.toolbar2.AddTool(203, _('Close all windows'), wx.Bitmap(self.currentdir+"/data/stop.png"))
		self.Bind(wx.EVT_TOOL, self.onStopAllVisual, stopvisual)

		names = wx.BoxSizer(wx.VERTICAL)
		names.AddSpacer(35)
		names.Add(normalLabel, 0, wx.ALL | wx.EXPAND, 10)
		names.AddSpacer(5)
		names.Add(alertLabel, 0, wx.ALL | wx.EXPAND, 10)
		names.AddSpacer(5)
		names.Add(warnLabel, 0, wx.ALL | wx.EXPAND, 10)
		names.AddSpacer(5)
		names.Add(alarmLabel, 0, wx.ALL | wx.EXPAND, 10)
		names.AddSpacer(5)
		names.Add(emergencyLabel, 0, wx.ALL | wx.EXPAND, 10)

		colours = wx.BoxSizer(wx.VERTICAL)
		colours.AddSpacer(30)
		colours.Add(self.visualNormal, 0, wx.ALL | wx.EXPAND, 5)
		colours.Add(self.visualAlert, 0, wx.ALL | wx.EXPAND, 5)
		colours.Add(self.visualWarn, 0, wx.ALL | wx.EXPAND, 5)
		colours.Add(self.visualAlarm, 0, wx.ALL | wx.EXPAND, 5)
		colours.Add(self.visualEmergency, 0, wx.ALL | wx.EXPAND, 5)

		auto = wx.BoxSizer(wx.VERTICAL)
		auto.AddSpacer(30)
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

		self.readColours()

	def readColours(self):
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
		filesLabel = wx.StaticText(self.soundMethod, label=_('File'))

		playButtonImg = wx.Bitmap(self.currentdir+"/data/play.png", wx.BITMAP_TYPE_ANY)

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

		self.toolbar5 = wx.ToolBar(self.soundMethod, style=wx.TB_TEXT | wx.TB_VERTICAL)
		save2 = self.toolbar5.AddTool(501, _('Save'), wx.Bitmap(self.currentdir+"/data/apply.png"))
		self.Bind(wx.EVT_TOOL, self.onSave3, save2)
		cancel2 = self.toolbar5.AddTool(502, _('Cancel'), wx.Bitmap(self.currentdir+"/data/cancel.png"))
		self.Bind(wx.EVT_TOOL, self.onCancel3, cancel2)
		self.toolbar5.AddSeparator()
		stopsounds = self.toolbar5.AddTool(503, _('Stop all sounds'), wx.Bitmap(self.currentdir+"/data/stop.png"))
		self.Bind(wx.EVT_TOOL, self.onStopAllSounds, stopsounds)

		names = wx.BoxSizer(wx.VERTICAL)
		names.AddSpacer(35)
		names.Add(normalLabel, 0, wx.ALL | wx.EXPAND, 10)
		names.AddSpacer(5)
		names.Add(alertLabel, 0, wx.ALL | wx.EXPAND, 10)
		names.AddSpacer(5)
		names.Add(warnLabel, 0, wx.ALL | wx.EXPAND, 10)
		names.AddSpacer(5)
		names.Add(alarmLabel, 0, wx.ALL | wx.EXPAND, 10)
		names.AddSpacer(5)
		names.Add(emergencyLabel, 0, wx.ALL | wx.EXPAND, 10)

		title = wx.BoxSizer(wx.HORIZONTAL)
		title.Add(filesLabel, 1, wx.ALL | wx.EXPAND, 5)

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
		sounds.Add(title, 0, wx.EXPAND, 0)
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

		self.readSounds()

	def readSounds(self):
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
			soundAlarm = ['/usr/share/sounds/openplotter/House_Fire_Alarm.mp3', False]
			self.conf.set('NOTIFICATIONS', 'soundAlarm', str(soundAlarm))
		try: 
			self.soundAlarm.SetValue(soundAlarm[0])
			self.alarmStop.SetValue(soundAlarm[1])
		except: pass

		try: soundEmergency = eval(self.conf.get('NOTIFICATIONS', 'soundEmergency'))
		except: 
			soundEmergency = ['/usr/share/sounds/openplotter/Tornado_Siren_II.mp3', False]
			self.conf.set('NOTIFICATIONS', 'soundEmergency', str(soundEmergency))
		try: 
			self.soundEmergency.SetValue(soundEmergency[0])
			self.emergencyStop.SetValue(soundEmergency[1])
		except: pass

	def onPlayButton(self,e):
		select = e.GetId()
		try:
			subprocess.call(['pkill','-15','vlc'])
			if select == 6001: subprocess.Popen(['cvlc', '--play-and-exit', self.soundNormal.GetValue()])
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
			if select == 5001: self.soundNormal.SetValue(dlg.GetPath())
			elif select == 5002: self.soundAlert.SetValue(dlg.GetPath())
			elif select == 5003: self.soundWarn.SetValue(dlg.GetPath())
			elif select == 5004: self.soundAlarm.SetValue(dlg.GetPath())
			elif select == 5005: self.soundEmergency.SetValue(dlg.GetPath())
		dlg.Destroy()

	def onSave3(self,e):
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

	def pageCommand(self):
		text1 = wx.StaticText(self.command, label=_('Coming soon.'))
		hbox1 = wx.BoxSizer(wx.HORIZONTAL)
		hbox1.AddStretchSpacer(1)
		hbox1.Add(text1, 0, wx.ALL | wx.EXPAND, 5)
		hbox1.AddStretchSpacer(1)
		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.AddStretchSpacer(1)
		vbox.Add(hbox1, 0, wx.ALL | wx.EXPAND, 5)
		vbox.AddStretchSpacer(1)
		self.command.SetSizer(vbox)

	############################################################################

	def pageSK(self):
		text1 = wx.StaticText(self.sk, label=_('Coming soon.'))
		hbox1 = wx.BoxSizer(wx.HORIZONTAL)
		hbox1.AddStretchSpacer(1)
		hbox1.Add(text1, 0, wx.ALL | wx.EXPAND, 5)
		hbox1.AddStretchSpacer(1)
		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.AddStretchSpacer(1)
		vbox.Add(hbox1, 0, wx.ALL | wx.EXPAND, 5)
		vbox.AddStretchSpacer(1)
		self.sk.SetSizer(vbox)

################################################################################

def main():
	try:
		platform2 = platform.Platform()
		if not platform2.postInstall(version,'notifications'):
			subprocess.Popen(['openplotterPostInstall', platform2.admin+' notificationsPostInstall'])
			return
	except: pass

	app = wx.App()
	MyFrame().Show()
	time.sleep(1)
	app.MainLoop()

if __name__ == '__main__':
	main()
