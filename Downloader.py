# -*- coding: utf-8 -*-
import wx
import wx.adv as adv
import urllib
import urllib2
import re
import threading
import time,os,sys
import codecs as cd
import requests
import webbrowser
import random
import string
from dict_data import dict_strlist,strlist_dict,NotDictStrError
import traceback

_encoding='utf8'  # write and read file data
_systemencoding='gb2312'  # pass file name to os.system
_webencoding='utf8'  # match web page
charRep={
	'\\':'[',
	'/':']',
	'*':'^',
	':':';',
	'"':'\'',
	'<':u'《',
	'>':u'》',
	'|':'!',
	'?':'$'}

def WebSolve(path,sets):
	error={'title':'','url':''}
	req = urllib2.urlopen(path,timeout=20)
	content = req.read()
	# Search title and filename
	if sets['title']['type']=='random':
		title=sets['title']['string']+''.join(random.sample(string.ascii_lowercase,sets['title']['int']))
	elif sets['title']['type']=='custom':
		title_regex=sets['title']['string'].split('\n')
		t=content
		i=1
		for regex in title_regex:
			res=re.findall(regex.encode(_webencoding),t, re.IGNORECASE)
			if len(res)>0:
				t=res[0]
				i+=1
			else:
				error['title']='can\'t find a match at [line %d]'%i
				if i!=1:
					error['title']+=' in [ %s ]'%t.decode(_webencoding)
				t=''
				break
		title=t.decode(_webencoding)
	filename='%s.%s'%(title,sets['title']['ext'])

	for key in charRep:
		filename=filename.replace(key,charRep[key])
	
	# Search download URL
	url_regex=sets['url'].split('\n')
	u=content
	i=1
	for regex in url_regex:
		res=re.findall(regex.encode(_webencoding),u, re.IGNORECASE)
		if len(res)>0:
			u=res[0]
			i+=1
		else:
			error['url']='can\'t find a match at line %d'%i
			if i!=1:
				error['url']+=' in [ %s ]'%u.decode(_webencoding)
			u=''
			break
	url=u.decode(_webencoding)
	
	return title,filename,url,error

class StopError(RuntimeError):
	def __init__(self,message):
		self.msg=message

class MainFrame ( wx.Frame ):
	
	def __init__( self ):
		wx.Frame.__init__ ( self, None,id = wx.ID_ANY, title = u"Web Downloder", pos = wx.DefaultPosition, size = wx.Size( 600,400 ), style = wx.DEFAULT_FRAME_STYLE|wx.STAY_ON_TOP|wx.TAB_TRAVERSAL )
		
		# Variables
		self.suspendScan=False
		self.last_path=''
		self.settings=[]
		"""
		sets={'id':'edfg','domain':'www.baidu.com','title':{'type':'random|custom','string':'prefix|regex','int':'count|auto','ext':'extension'},'url':'regex'}
		"""
		self.TaskList=[]
		# UI
		self.SetSizeHints( wx.Size( 500,300 ), wx.DefaultSize )
		self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )
		
		bSizer1 = wx.BoxSizer( wx.VERTICAL )
		
		bSizer2 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_staticText1 = wx.StaticText( self, wx.ID_ANY, u"Folder：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText1.Wrap( -1 )
		bSizer2.Add( self.m_staticText1, 0, wx.ALIGN_CENTER|wx.ALL, 5 )
		
		self.DefaultFolder = wx.DirPickerCtrl( self, wx.ID_ANY, wx.EmptyString, u"默认下载目录", wx.DefaultPosition, wx.DefaultSize, wx.DIRP_DEFAULT_STYLE )
		bSizer2.Add( self.DefaultFolder, 1, wx.ALL|wx.EXPAND, 5 )
		
		bSizer1.Add( bSizer2, 0, wx.EXPAND, 5 )
		
		self.m_staticline1 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer1.Add( self.m_staticline1, 0, wx.EXPAND |wx.ALL, 5 )
		
		bSizer47 = wx.BoxSizer( wx.HORIZONTAL )
		
		
		bSizer47.AddSpacer( 15 )
		
		self.CheckAll = wx.CheckBox( self, wx.ID_ANY, wx.EmptyString, wx.Point( -1,-1 ), wx.DefaultSize, wx.CHK_3STATE )
		bSizer47.Add( self.CheckAll, 0, wx.ALL, 5 )
		
		self.m_staticline3 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_VERTICAL )
		bSizer47.Add( self.m_staticline3, 0, wx.EXPAND |wx.ALL, 5 )
		
		
		bSizer47.AddStretchSpacer( -1 )
		
		self.ScanEnable = wx.CheckBox( self, wx.ID_ANY, u"Enable Scan", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.ScanEnable.SetValue(False)
		self.ScanEnable.Enable(False)
		bSizer47.Add( self.ScanEnable, 0, wx.ALL, 5 )
		
		bSizer1.Add( bSizer47, 0, wx.EXPAND, 5 )
		
		self.Tab = wx.Notebook( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.DownloadWindow = wx.ScrolledWindow( self.Tab, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.VSCROLL )
		self.DownloadWindow.SetScrollRate( 5, 5 )
		self.DownloadList = wx.BoxSizer( wx.VERTICAL )
		
		self.DownloadWindow.SetSizer( self.DownloadList )
		self.DownloadWindow.Layout()
		self.DownloadList.Fit( self.DownloadWindow )
		self.Tab.AddPage( self.DownloadWindow, u"Downloading", False )
		self.FinishWindow = wx.ScrolledWindow( self.Tab, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.VSCROLL )
		self.FinishWindow.SetScrollRate( 5, 5 )
		bSizer50 = wx.BoxSizer( wx.VERTICAL )
		
		FinishListChoices = []
		self.FinishList = wx.ListBox( self.FinishWindow, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, FinishListChoices, 0|wx.NO_BORDER )
		bSizer50.Add( self.FinishList, 1, wx.ALL|wx.EXPAND, 0 )
		
		self.FinishWindow.SetSizer( bSizer50 )
		self.FinishWindow.Layout()
		bSizer50.Fit( self.FinishWindow )
		self.Tab.AddPage( self.FinishWindow, u"Finished", False )
		
		bSizer1.Add( self.Tab, 1, wx.EXPAND |wx.ALL, 5 )
		

		bSizer26 = wx.BoxSizer( wx.HORIZONTAL )
		
		
		bSizer26.AddStretchSpacer()
		
		self.SettingBtn = wx.Button( self, wx.ID_ANY, u"Settings", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer26.Add( self.SettingBtn, 0, wx.ALIGN_CENTER|wx.ALL, 5 )
		
		self.CloseBtn = wx.Button( self, wx.ID_ANY, u"Close", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer26.Add( self.CloseBtn, 0, wx.ALIGN_RIGHT|wx.ALL, 5 )
		
		bSizer1.Add( bSizer26, 0, wx.EXPAND, 5 )
		
		self.SetSizer( bSizer1 )
		self.Layout()
		
		self.Centre( wx.BOTH )
		
		# Connect Events
		self.DefaultFolder.Bind( wx.EVT_DIRPICKER_CHANGED, self.FolderChange )
		self.ScanEnable.Bind( wx.EVT_CHECKBOX, self.ScanCheck )
		self.FinishList.Bind( wx.EVT_LISTBOX_DCLICK, self.OpenFile )
		self.SettingBtn.Bind( wx.EVT_BUTTON, self.settingwindow )
		self.CloseBtn.Bind( wx.EVT_BUTTON, self.close )

		self.loadSettings()

		# scan event and thread
		self.scan_evt=threading.Event()
		st=threading.Thread(target=self.ScanThread)
		st.setDaemon(True)
		st.start()
	
	def loadSettings(self):
		work_dir=os.path.dirname(sys.argv[0])
		setting_path=os.path.join(work_dir,"setting.ini")
		if os.path.exists(setting_path):
			with cd.open(setting_path,encoding=_encoding) as f:
				data=f.readlines()
				self.settings=strlist_dict(data)['settings']
		else:
			self.settings=[]

	def FolderChange( self, event ):
		self.ScanEnable.Enable()
		event.Skip()
	
	def ScanCheck( self, event ):
		if event.IsChecked():
			self.scan_evt.set()
		else:
			self.scan_evt.clear()
		event.Skip()

	def ScanThread(self):
		while True:
			if self.scan_evt.is_set() and not self.suspendScan:
				text_data = wx.TextDataObject()
				if wx.TheClipboard.Open():
					success = wx.TheClipboard.GetData(text_data)
					wx.TheClipboard.Close()
				if success:
					path=text_data.GetText()
					if path!=self.last_path:
						self.last_path=path
						for sets in self.settings:
							if sets['domain'] in path:
								wx.CallAfter(self.StartNewDownload,path,sets)
								break
			#loop downloading list
			Children=self.DownloadList.GetChildren()
			for child in Children:
				child=child.GetWindow()
				if child.task['complete']:
					self.FinishList.Append(child.task['title'],child.task)
					child.DestroyLater()

			time.sleep(1)
		
	def StartNewDownload(self,path,sets):
		self.Freeze()
		id=''.join(random.sample(string.ascii_lowercase,4))
		task={'id':id,'source':path,'setting':sets,'folder':self.DefaultFolder.GetPath(),'complete':False}
		self.TaskList.append(task)
		item=DownloadItem(self.DownloadWindow,task)
		self.DownloadList.Add(item,0, wx.ALL|wx.EXPAND, 5)
		self.DownloadWindow.Layout()
		self.DownloadList.Fit( self.DownloadWindow )
		item.start()
		self.Layout()
		self.Thaw()

	def OpenFile( self, event ):
		task=event.GetClientData()
		filename=task['filename']
		if os.path.exists(filename):
			os.system(filename.encode(_systemencoding))
		else:
			res=wx.MessageDialog(None, 'File is not existed!\n\nDo you want to re-download it?',"Info",wx.YES_NO|wx.NO_DEFAULT|wx.ICON_QUESTION).ShowModal()
			if res==wx.ID_YES:
				source=task['source']
				self.TaskList.remove(task)
				self.FinishList.Delete(event.GetSelection())
				wx.CallAfter(self.StartNewDownload,source)
		if event is not None: event.Skip()
	
	def settingwindow( self, event ):
		sf=SettingFrame(self,self.settings)
		sf.Show()
		if event is not None: event.Skip()
	
	def close( self, event ):
		self.Close()
		if event is not None: event.Skip()
class DownloadItem ( wx.Panel ):
	
	def __init__( self, parent,task):
		wx.Panel.__init__ ( self,parent )

		# Variables
		self.task=task 
		"""
		task keys:
			id
			source : page URL
			setting : search settings
			folder : Saving folder
			complete
			title : video title
			filename : File path in local
		"""
		
		self.lastupdate=None
		self.lastsize=0
		self.StopEvt=threading.Event()
		self.DelEvt=threading.Event()
		
		# UI
		self.Item = wx.BoxSizer( wx.VERTICAL )

		bSizer34 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_panel6 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( 5,-1 ), wx.TAB_TRAVERSAL )
		self.m_panel6.SetBackgroundColour( wx.Colour( 130, 192, 255 ) )
		
		bSizer34.Add( self.m_panel6, 0, wx.EXPAND |wx.ALL, 0 )
		
		self.SelectedChecker = wx.CheckBox( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer34.Add( self.SelectedChecker, 0, wx.ALL, 5 )
		
		bSizer7 = wx.BoxSizer( wx.VERTICAL )
		
		bSizer19 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.FileName = adv.HyperlinkCtrl( self, wx.ID_ANY, wx.EmptyString, '', wx.DefaultPosition, wx.DefaultSize, 0|wx.NO_BORDER )
		
		self.FileName.SetNormalColour( wx.Colour( 48, 48, 48 ) )
		self.FileName.SetFont( wx.Font( 10, 70, 90, 92, False, wx.EmptyString ) )
		
		bSizer19.Add( self.FileName, 1, wx.ALL|wx.EXPAND, 5 )
		
		self.m_button4 = wx.Button( self, wx.ID_ANY, u"Source", wx.DefaultPosition, wx.Size( -1,24 ) )
		bSizer19.Add( self.m_button4, 0, wx.ALIGN_CENTER|wx.ALL, 2 )
		
		self.m_button41 = wx.Button( self, wx.ID_ANY, u"Resolve", wx.DefaultPosition,wx.Size( -1,24 ) )
		bSizer19.Add( self.m_button41, 0, wx.ALIGN_CENTER|wx.ALL, 2 )
		
		self.m_button42 = wx.Button( self, wx.ID_ANY, u"Delete", wx.DefaultPosition, wx.Size( -1,24 ) )
		bSizer19.Add( self.m_button42, 0, wx.ALIGN_CENTER|wx.ALL, 2 )
		
		bSizer7.Add( bSizer19, 1, wx.EXPAND, 5 )
		
		self.ProgressBar = wx.Gauge( self, wx.ID_ANY, 100, wx.DefaultPosition, wx.Size( -1,5 ), wx.GA_HORIZONTAL )
		bSizer7.Add( self.ProgressBar, 0, wx.ALIGN_CENTER|wx.ALL|wx.EXPAND, 5 )
		
		bSizer6 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.VideoSize = wx.StaticText( self, wx.ID_ANY, u"0B", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.VideoSize.Wrap( -1 )
		bSizer6.Add( self.VideoSize, 1, wx.ALIGN_CENTER|wx.ALL, 5 )
		
		
		self.TimeRemain = wx.StaticText( self, wx.ID_ANY, u"00:00:00", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.TimeRemain.Wrap( -1 )
		bSizer6.Add( self.TimeRemain, 1, wx.ALL, 5 )
		
		
		self.Spead = wx.StaticText( self, wx.ID_ANY, u"0B/s", wx.DefaultPosition, wx.Size( 75,-1 ), wx.ALIGN_RIGHT )
		self.Spead.Wrap( -1 )
		bSizer6.Add( self.Spead, 0, wx.ALL, 5 )
		
		bSizer7.Add( bSizer6, 0, wx.EXPAND, 5 )
		
		bSizer34.Add( bSizer7, 1, 0, 5 )
		
		self.Item.Add( bSizer34, 1, wx.EXPAND, 5 )
		
		self.m_staticline4 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		self.Item.Add( self.m_staticline4, 0, wx.EXPAND |wx.ALL, 0 )
		
		
		self.Item.AddSpacer( 5 )
		self.SetSizer( self.Item )
		# Connect Events
		self.FileName.Bind( adv.EVT_HYPERLINK, self.checkExistance )
		self.m_button4.Bind( wx.EVT_BUTTON, self.OpenSource )
		self.m_button41.Bind( wx.EVT_BUTTON, self.Resolve )
		self.m_button42.Bind( wx.EVT_BUTTON, self.Delete )

	def start( self ):
		t=threading.Thread(target=self.download)
		t.setDaemon(True)
		t.start()
		
	def download(self):
		while not self.DelEvt.is_set():
			try:
				self.FileName.SetLabelText('Solving...')
				self.FileName.SetURL(self.task['folder'])  # click to open saving folder
				self.ProgressBar.SetValue(0)
				self.ProgressBar.Pulse()
				self.VideoSize.LabelText='0B'
				self.TimeRemain.LabelText='00:00:00'
				self.Spead.LabelText='0B/s'

				if self.task['source']:
					title,filename,url,error=WebSolve(self.task['source'],self.task['setting'])
					if self.StopEvt.is_set():
						continue
					if self.DelEvt.is_set():
						break
					
					self.FileName.SetLabelText(title)
					self.task['title']=title

					#check for file existance
					self.task['filename']="%s\\%s"%(self.task['folder'],filename)
					i=1
					tempname=self.task['filename']
					while os.path.exists(tempname) and self.task['setting']['title']['int']:
						p=os.path.splitext(filename)
						tempname='%s[%d]%s'%(p[0],i,p[1])
						i+=1
					self.task['filename']=tempname

					# start download
					self.lastupdate=time.time()
					urllib.urlretrieve(url, self.task['filename'], reporthook=self.ProgressReport)
					self.task['complete']=True
					self.FileName.SetURL(self.task['filename'])

				break
			except StopError:
				self.StopEvt.clear()
				continue
			except:
				self.StopEvt.clear()
				print traceback.format_exc()
				continue
		if self.DelEvt.is_set():
			self.DestroyLater()

	def checkExistance( self, event ):
		if event is not None: event.Skip()
	
	def OpenSource( self, event ):
		webbrowser.open(self.task['source'])
		if event is not None: event.Skip()
	
	def Resolve( self, event ):
		if self.task['complete']:
			res=wx.MessageDialog(None, \
							'Do you want to re-download?\n\n \
							Existing file will be deleted.\n', \
							"Info",wx.YES_NO|wx.NO_DEFAULT|wx.ICON_QUESTION).ShowModal()
			if res==wx.ID_YES:
				self.task['complete']=False
				self.start()
		else:
			self.StopEvt.set()
		if event is not None: event.Skip()

	def ProgressReport(self,count, blockSize, totalSize):
		if not self.StopEvt.is_set():
			currentSize=count*blockSize
			percent = int(currentSize*100/totalSize)
			self.ProgressBar.SetValue(percent)
			t_size=''
			if totalSize<1024:
				size='%dB'%totalSize
			elif totalSize<pow(1024,2):
				size='%.2fKB'%(totalSize/1024)
			elif totalSize<pow(1024,3):
				size='%.2fMB'%(totalSize/pow(1024,2))
			elif totalSize<pow(1024,4):
				size='%.2fGB'%(totalSize/pow(1024,3))

			self.VideoSize.LabelText='%s/%s'%(self.ConvSize(currentSize),self.ConvSize(totalSize))

			sizechange=currentSize-self.lastsize  # in Bytes
			timechange=time.time()-self.lastupdate   # in seconds
			
			if timechange!=0:
				self.Spead.LabelText='%s/s'%self.ConvSize(sizechange/timechange)
				if sizechange!=0:
					timeRemain=time.gmtime((totalSize-currentSize)/(sizechange/timechange))
					self.TimeRemain.LabelText= '%2d:%2d:%2d'%(timeRemain[3],timeRemain[4],timeRemain[5])
				else:
					self.TimeRemain.LabelText= '--:--:--'
		else:
			raise StopError('Downloading stopped!')
		

	def ConvSize(self,size):
		if size<1024:
			return '%dB'%size
		elif size<pow(1024,2):
			return '%.2fKB'%(size/1024.)
		elif size<pow(1024,3):
			return '%.2fMB'%(size/pow(1024.,2))
		else:
			return '%.2fGB'%(size/pow(1024.,3))

	def Delete( self, event ):
		self.DelEvt.set()
		self.StopEvt.set()
		self.Parent.Parent.DownloadList.Detach(self)  # detach self from sizer with destorying it
		self.Parent.Layout()
		if self.task['complete']:
			self.DestroyLater()
		if event is not None: event.Skip()
	
class SettingFrame ( wx.Frame ):
	
	def __init__( self, parent,settings ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"Settings", pos = wx.DefaultPosition, size = wx.Size( 610,350 ), style = wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT|wx.FRAME_NO_TASKBAR|wx.FRAME_TOOL_WINDOW|wx.RESIZE_BORDER|wx.TAB_TRAVERSAL )
		
		# Variables
		self.settings=settings

		# UI
		self.SetSizeHints( wx.Size( 610,380 ), wx.DefaultSize )
		self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )
		
		bSizer17 = wx.BoxSizer( wx.HORIZONTAL )
		
		sbSizer2 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Domain" ), wx.VERTICAL )
		
		DomainListChoices = []
		self.DomainList = wx.ListBox( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( 150,-1 ), DomainListChoices, 0 )
		sbSizer2.Add( self.DomainList, 1, wx.ALL, 5 )
		
		bSizer18 = wx.BoxSizer( wx.HORIZONTAL )
		
		
		bSizer18.AddStretchSpacer( 1 )
		
		self.m_button8 = wx.Button( self, wx.ID_ANY, u"+", wx.DefaultPosition, wx.Size( 22,22 ), wx.BU_EXACTFIT )
		bSizer18.Add( self.m_button8, 0, wx.ALL, 5 )
		
		self.m_button9 = wx.Button( self, wx.ID_ANY, u"-", wx.DefaultPosition, wx.Size( 22,22 ), 0 )
		bSizer18.Add( self.m_button9, 0, wx.ALL|wx.EXPAND, 5 )
		
		sbSizer2.Add( bSizer18, 0, wx.EXPAND, 5 )
		
		bSizer17.Add( sbSizer2, 0, wx.EXPAND, 5 )
		
		
		bSizer17.AddSpacer( 5 )
		
		sbSizer3 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Details" ), wx.VERTICAL )
		
		self.DomainName = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		sbSizer3.Add( self.DomainName, 0, wx.ALL|wx.EXPAND, 5 )
		
		sbSizer4 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Title/Filename determine" ), wx.HORIZONTAL )
		
		bSizer19 = wx.BoxSizer( wx.VERTICAL )
		
		bSizer20 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.radioRandom = wx.RadioButton( self, wx.ID_ANY, u"Random String:", wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
		bSizer20.Add( self.radioRandom, 0, wx.ALIGN_CENTER|wx.ALL, 5 )
		
		self.RandomPrefix = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.RandomPrefix.Enable(False)
		bSizer20.Add( self.RandomPrefix, 1, wx.ALL, 5 )
		
		
		self.m_staticText8 = wx.StaticText( self, wx.ID_ANY, u"+", wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
		self.m_staticText8.Wrap( -1 )
		bSizer20.Add( self.m_staticText8, 0, wx.ALIGN_CENTER|wx.ALL, 5 )
		
		self.RandomCount = wx.SpinCtrl( self, wx.ID_ANY, u"0", wx.DefaultPosition, wx.Size( 50,-1 ), wx.SP_ARROW_KEYS, 4, 16, 8 )
		self.RandomCount.Enable(False)
		bSizer20.Add( self.RandomCount, 0, wx.ALL, 5 )
		
		self.m_staticText81 = wx.StaticText( self, wx.ID_ANY, u"chars", wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
		self.m_staticText81.Wrap( -1 )
		bSizer20.Add( self.m_staticText81, 0, wx.ALIGN_CENTER|wx.ALL, 5 )
		
		bSizer19.Add( bSizer20, 0, wx.EXPAND, 5 )
		
		bSizer21 = wx.BoxSizer( wx.HORIZONTAL )
		
		bSizer23 = wx.BoxSizer( wx.VERTICAL )
		
		self.radioCustom = wx.RadioButton( self, wx.ID_ANY, u"Custom:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.radioCustom.SetValue( True ) 
		bSizer23.Add( self.radioCustom, 0, wx.ALL, 5 )
		
		self.AutoNumber = wx.CheckBox( self, wx.ID_ANY, u"Auto", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.AutoNumber.SetValue(True) 
		bSizer23.Add( self.AutoNumber, 0, wx.ALIGN_RIGHT|wx.ALL, 5 )
		
		bSizer21.Add( bSizer23, 0, wx.EXPAND, 5 )
		
		bSizer24 = wx.BoxSizer( wx.VERTICAL )
		
		self.TitleSearchRule = wx.TextCtrl( self, wx.ID_ANY, u"", wx.DefaultPosition, wx.Size( -1,65 ), wx.TE_MULTILINE )
		bSizer24.Add( self.TitleSearchRule, 1, wx.ALL|wx.EXPAND, 5 )
		
		bSizer21.Add( bSizer24, 1, wx.EXPAND, 5 )
		
		bSizer19.Add( bSizer21, 0, wx.EXPAND, 5 )
		
		sbSizer4.Add( bSizer19, 1, wx.EXPAND, 5 )
		
		self.m_staticline5 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_VERTICAL )
		sbSizer4.Add( self.m_staticline5, 0, wx.EXPAND |wx.ALL, 5 )
		
		self.m_staticText19 = wx.StaticText( self, wx.ID_ANY, u".", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText19.Wrap( -1 )
		sbSizer4.Add( self.m_staticText19, 0, wx.ALIGN_CENTER|wx.ALL, 5 )
		
		self.fileExt = wx.TextCtrl( self, wx.ID_ANY, u"", wx.DefaultPosition, wx.Size( 50,-1 ), 0 )
		sbSizer4.Add( self.fileExt, 0, wx.ALIGN_CENTER|wx.ALL, 0 )
		
		sbSizer3.Add( sbSizer4, 0, wx.EXPAND, 5 )
		
		sbSizer5 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Download URL" ), wx.VERTICAL )
		
		self.URLSearchRule = wx.TextCtrl( self, wx.ID_ANY, u"", wx.DefaultPosition, wx.Size( -1,-1 ), wx.TE_MULTILINE )
		sbSizer5.Add( self.URLSearchRule, 1, wx.ALL|wx.EXPAND, 5 )
		
		sbSizer3.Add( sbSizer5, 1, wx.EXPAND, 5 )
		
		bSizer22 = wx.BoxSizer( wx.HORIZONTAL )
		
		
		bSizer22.AddStretchSpacer( 1 )

		self.m_button10 = wx.Button( self, wx.ID_ANY, u"Test", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer22.Add( self.m_button10, 0, wx.ALL, 5 )

		self.m_button11 = wx.Button( self, wx.ID_ANY, u"Save", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer22.Add( self.m_button11, 0, wx.ALL, 5 )
		
		self.m_button12 = wx.Button( self, wx.ID_ANY, u"Reset", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer22.Add( self.m_button12, 0, wx.ALL, 5 )
		
		sbSizer3.Add( bSizer22, 0, wx.EXPAND, 5 )
		
		bSizer17.Add( sbSizer3, 1, wx.EXPAND, 5 )
		
		self.SetSizer( bSizer17 )
		self.Layout()
		
		self.Centre( wx.BOTH )
		
		# Connect Events
		self.DomainList.Bind( wx.EVT_LISTBOX, self.ReadDetail )
		self.m_button8.Bind( wx.EVT_BUTTON, self.addDomain )
		self.m_button9.Bind( wx.EVT_BUTTON, self.removeDomain )
		self.radioRandom.Bind( wx.EVT_RADIOBUTTON, self.TitleChoose )
		self.radioCustom.Bind( wx.EVT_RADIOBUTTON, self.TitleChoose )
		self.m_button10.Bind( wx.EVT_BUTTON, self.TestSetting )
		self.m_button11.Bind( wx.EVT_BUTTON, self.Save )
		self.m_button12.Bind( wx.EVT_BUTTON, self.ReadDetail )
		self.Bind( wx.EVT_CLOSE, self.OnClose )

		self.Parent.suspendScan=True
		self.setDomainList()

	def OnClose(self,event):
		self.Parent.suspendScan=False
		event.Skip()

	def setDomainList( self ):
		"""
		sets={'id':'edfg','domain':'www.baidu.com','title':{'type':'random|custom','string':'prefix|regex','int':'count|auto','ext':'extension'},'url':'regex'}
		"""
		self.Freeze()
		self.DomainList.Clear()
		if self.settings is not None and len(self.settings)!=0:
			for sets in self.settings:
				self.DomainList.Append(sets['domain'],sets)
		if self.DomainList.GetCount()>0:
			self.DomainList.SetSelection(0)
			self.ReadDetail(None)
		self.Thaw()

	def addDomain( self, event ):
		self.Freeze()
		id=''.join(random.sample(string.ascii_lowercase,4))
		#sets={'id':id,'domain':'<new Domain>','title':{'type':'custom','string':'<title>(.*)</title>','int':1,'ext':'mp4'},'url':'setVideoUrlHigh(\'(http[^;]*[0-9,a-z])\');'}
		sets={'id':id,'domain':'<new Domain>','title':{'type':'custom','string':'<title>(.*)</title>','int':1,'ext':'mp4'},'url':''}
		self.settings.append(sets)
		self.DomainList.Append(sets['domain'],sets)
		self.DomainList.SetSelection(self.DomainList.GetCount()-1)
		self.ReadDetail(None)
		self.Thaw()
		event.Skip()
	
	def removeDomain( self, event ):
		index=self.DomainList.GetSelection()
		if index!=-1:
			res=wx.MessageDialog(None, 'Selected domain can be lost forever!\n\nContinue?',"Info",wx.YES_NO|wx.NO_DEFAULT|wx.ICON_QUESTION).ShowModal()
			if res==wx.ID_YES:
				self.Freeze()
				sets=self.DomainList.GetClientData(index)
				self.settings.remove(sets)
				self.DomainList.Delete(index)
				if self.DomainList.GetCount()-1>=index:
					self.DomainList.SetSelection(index)
					self.ReadDetail(None)
				else:
					self.DomainList.SetSelection(index-1)
					self.ReadDetail(None)
				self.Thaw()	
		self.saveSettings()
		event.Skip()
	
	def TitleChoose( self, event ):
		label=event.GetEventObject().GetLabel()
		self.RadioSet(label)
		event.Skip()
	
	def RadioSet(self,choice):
		if 'random' in choice.lower():
			self.RandomPrefix.Enable(True)
			self.RandomCount.Enable(True)
			self.TitleSearchRule.Enable(False)
			self.AutoNumber.Enable(False)
		elif 'custom' in choice.lower():
			self.RandomPrefix.Enable(False)
			self.RandomCount.Enable(False)
			self.TitleSearchRule.Enable(True)
			self.AutoNumber.Enable(True)

	def Save( self, event ):
		index=self.DomainList.GetSelection()
		if index!=-1:
			# Organsize the setting table information
			newSets=self.OrganiseSetting()
			if newSets is None: return
			sets=self.DomainList.GetClientData(index)
			sets.update(newSets)
			
			# update the string displayed in list
			self.DomainList.SetString(index,self.DomainName.Value)

			# save to local disk
			self.saveSettings()
		event.Skip()
	
	def OrganiseSetting(self):
		# validate settings first
		if self.DomainName.Value=='':
			wx.MessageDialog(self,'Invalid domain name','Validate').ShowModal()
			return None
		if self.radioRandom.Value:
			for k in charRep:
				if k in self.RandomPrefix.Value:
					wx.MessageDialog(self,'Invalid title prefix string\n\nDo not use \\/*:\"<>|? in title, they are not allowed in file name.','Validate').ShowModal()
					return None
		if self.radioCustom.Value:
			if self.TitleSearchRule.Value=='':
				wx.MessageDialog(self,'Empty Regex code in title searching\n\nEnter at least one line.','Validate').ShowModal()
				return None
		if self.fileExt.Value=='':
			wx.MessageDialog(self,'Empty file extension','Validate').ShowModal()
			return None
		else:
			for k in charRep:
				if k in self.fileExt.Value:
					wx.MessageDialog(self,'Invalid file extension string\n\nDo not use \\/*:\"<>|?, they are not allowed in file name.','Validate').ShowModal()
					return None
		if self.URLSearchRule.Value=='':
			wx.MessageDialog(self,'Empty Regex code in url searching\n\nEnter at least one line.','Validate').ShowModal()
			return None
		# setting is validated.
		# write data to sets
		newSets={
			'domain':self.DomainName.Value,
			'title':{
				'type':'custom' if self.radioCustom.Value else 'random',
				'string':self.TitleSearchRule.Value if self.radioCustom.Value else self.RandomPrefix.Value,
				'int':int(self.AutoNumber.Value) if self.radioCustom.Value else self.RandomCount.Value,
				'ext':self.fileExt.Value
				},
			'url':self.URLSearchRule.Value
			}
		return newSets

	def ReadDetail( self, event ):
		"""
		sets={'id':'edfg','domain':'www.baidu.com','title':{'type':'random|custom','string':'prefix|regex','int':'count|auto','ext':'extension'},'url':'regex'}
		"""
		index=self.DomainList.GetSelection()
		if index!=-1:
			# apply data to UI elements
			sets=self.DomainList.GetClientData(index)
			self.DomainName.Value=sets['domain']
			if sets['title']['type']=='random':
				self.radioRandom.Value=True
				self.RandomPrefix.Value=sets['title']['string']
				self.RandomCount.Value=sets['title']['int']
				self.TitleSearchRule.Value=''
				self.AutoNumber.Value=False
			elif sets['title']['type']=='custom':
				self.radioCustom.Value=True
				self.RandomPrefix.Value=''
				self.RandomCount.Value=8
				self.TitleSearchRule.Value=sets['title']['string']
				self.AutoNumber.Value=sets['title']['int']
			self.RadioSet(sets['title']['type'])
			self.fileExt.Value=sets['title']['ext']
			self.URLSearchRule.Value=sets['url']
			
		else:
			# clear UI data
			self.DomainName.Value=''
			self.radioCustom.Value=True
			self.RandomPrefix.Value=''
			self.RandomCount.Value=8
			self.TitleSearchRule.Value=''
			self.AutoNumber.Value=False
			self.RadioSet('custom')
			self.fileExt.Value=''
			self.URLSearchRule.Value=''

		if event is not None: event.Skip()
	
	def saveSettings(self):
		work_dir=os.path.dirname(sys.argv[0])
		setting_path=os.path.join(work_dir,"setting.ini")
		if self.settings is not None and len(self.settings)!=0:
			with cd.open(setting_path,mode='w',encoding=_encoding) as f:
				data={'settings':self.settings}
				dict_strlist(data,file=f)
		else:
			if os.path.exists(setting_path):
				os.remove(setting_path)
	
	def TestSetting(self,event):
		# Organsize the setting table information
		newSets=self.OrganiseSetting()
		if newSets is None: return
		tsf=TestSettingFrame(self,newSets)
		tsf.Show()
		if event is not None: event.Skip()
		
class TestSettingFrame ( wx.Frame ):
	
	def __init__( self, parent,sets ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"TestPanel", pos = wx.DefaultPosition, size = wx.Size( 672,360 ), style = wx.CAPTION|wx.CLOSE_BOX|wx.FRAME_FLOAT_ON_PARENT|wx.FRAME_NO_TASKBAR|wx.FRAME_TOOL_WINDOW|wx.SYSTEM_MENU|wx.TAB_TRAVERSAL )
		
		# Variables
		self.sets=sets
		self.solveLock=threading.Event()

		# UI
		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
		self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )
		
		bSizer25 = wx.BoxSizer( wx.VERTICAL )
		
		bSizer26 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_staticText11 = wx.StaticText( self, wx.ID_ANY, u"Source URL:", wx.DefaultPosition, wx.Size( 70,-1 ), 0 )
		self.m_staticText11.Wrap( -1 )
		bSizer26.Add( self.m_staticText11, 0, wx.ALIGN_CENTER|wx.ALL, 5 )
		
		self.SourceURL = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer26.Add( self.SourceURL, 1, wx.ALIGN_CENTER|wx.ALL, 5 )
		
		self.SolveBtn = wx.Button( self, wx.ID_ANY, u"GO", wx.DefaultPosition, wx.Size( 40,-1 ), 0 )
		self.SolveBtn.SetDefault() 
		bSizer26.Add( self.SolveBtn, 0, wx.ALIGN_CENTER|wx.ALL, 5 )
		
		bSizer25.Add( bSizer26, 0, wx.EXPAND, 5 )
		
		bSizer31 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_staticText16 = wx.StaticText( self, wx.ID_ANY, u"Using:", wx.DefaultPosition, wx.Size( 70,-1 ), 0 )
		self.m_staticText16.Wrap( -1 )
		bSizer31.Add( self.m_staticText16, 0, wx.ALIGN_CENTER|wx.ALL, 5 )
		
		self.DomainName = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 250,-1 ), wx.TE_READONLY )
		bSizer31.Add( self.DomainName, 0, wx.ALL, 5 )
		
		bSizer25.Add( bSizer31, 0, wx.EXPAND, 5 )
		
		self.m_staticline6 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer25.Add( self.m_staticline6, 0, wx.EXPAND |wx.ALL, 5 )
		
		sbSizer5 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Title/Filename" ), wx.VERTICAL )
		
		bSizer27 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_staticText12 = wx.StaticText( self, wx.ID_ANY, u"Title:", wx.DefaultPosition, wx.Size( 70,-1 ), 0 )
		self.m_staticText12.Wrap( -1 )
		bSizer27.Add( self.m_staticText12, 0, wx.ALIGN_CENTER|wx.ALL, 5 )
		
		self.TitleStr = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_READONLY )
		bSizer27.Add( self.TitleStr, 1, wx.ALL, 5 )
		
		sbSizer5.Add( bSizer27, 0, wx.EXPAND, 5 )
		
		bSizer271 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_staticText121 = wx.StaticText( self, wx.ID_ANY, u"File name:", wx.DefaultPosition, wx.Size( 70,-1 ), 0 )
		self.m_staticText121.Wrap( -1 )
		bSizer271.Add( self.m_staticText121, 0, wx.ALIGN_CENTER|wx.ALL, 5 )
		
		self.Filename = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_READONLY )
		bSizer271.Add( self.Filename, 1, wx.ALL, 5 )
		
		sbSizer5.Add( bSizer271, 0, wx.EXPAND, 5 )
		
		bSizer25.Add( sbSizer5, 0, wx.EXPAND, 5 )
		
		sbSizer7 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Download URL" ), wx.HORIZONTAL )
		
		self.m_staticText15 = wx.StaticText( self, wx.ID_ANY, u"Target URL:", wx.DefaultPosition, wx.Size( 70,-1 ), 0 )
		self.m_staticText15.Wrap( -1 )
		sbSizer7.Add( self.m_staticText15, 0, wx.ALIGN_CENTER|wx.ALL, 5 )
		
		self.TargetURL = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,-1 ), wx.TE_MULTILINE|wx.TE_READONLY )
		sbSizer7.Add( self.TargetURL, 1, wx.ALL|wx.EXPAND, 5 )
		
		bSizer25.Add( sbSizer7, 1, wx.EXPAND, 5 )
		
		self.statusbar = wx.Gauge( self, wx.ID_ANY, 100, wx.DefaultPosition, wx.Size( -1,10 ), wx.GA_HORIZONTAL )
		bSizer25.Add( self.statusbar, 0, wx.ALL|wx.EXPAND, 5 )
		
		self.SetSizer( bSizer25 )
		self.Layout()
		
		self.Centre( wx.BOTH )
		
		# Connect Events
		self.SolveBtn.Bind( wx.EVT_BUTTON, self.Start )

		self.DomainName.Value=self.sets['domain']


	
	def Solve( self ):
		if self.SourceURL.Value!='':
			self.statusbar.Value=0
			self.statusbar.Pulse()
			self.TitleStr.Value=''
			self.Filename.Value=''
			self.TargetURL.Value=''
			title,filename,url,error=WebSolve(self.SourceURL.Value,self.sets)
			if error['title']=='':
				self.TitleStr.Value=title
				self.Filename.Value=filename
			else:
				self.TitleStr.Value=error['title']

			if error['url']=='':
				self.TargetURL.Value=url
			else:
				self.TargetURL.Value=error['url']
			self.statusbar.Value=100
		self.solveLock.clear()
		
	def Start(self,event):
		if self.solveLock.is_set(): return
		self.solveLock.set()
		t=threading.Thread(target=self.Solve)
		t.setDaemon(True)
		t.start()
		event.Skip()

app=wx.App()
app.frame=MainFrame()
app.frame.Show()
app.MainLoop()