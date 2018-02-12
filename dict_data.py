import random
import string
import collections as co
import re
import threading
try:
	import wx
	wx_imported=True
except ImportError:
	wx_imported=False

class NotDictStrError(RuntimeError):
	def __init__(self,message):
		self.msg=message

def dict_strlist(msg,parent=None,encoding=None,dialog=None,progress=1,file=None):
	
	key_pre=''
	type_pre=''
	value_pre=''
	
	if parent:
		key_pre=key_pre+parent+'.'

	data_str=[]
	keypath=nextlevel(msg,'')
	
	num=0.
	count=len(keypath)
	if dialog and wx_imported:
		signal = threading.Event()
		signal.set()
		dialog.Update(0)
		maximum=dialog.GetRange()
	
	for path in keypath:
		key_str=key_pre+path
		keys=path.split('.')
		v=None
		for k in keys:
			if v:
				v=v[k]
			else:
				v=msg[k]
		if v is None:
			type_str=type_pre+'none'
			value_str=value_pre+'none'
			full_msg_str='%s\0%s\0%s'%(key_str,type_str,value_str)
			full_msg_str=full_msg_str.encode(encoding) if encoding else full_msg_str
			data_str.append(full_msg_str)
			if file:file.write(full_msg_str+'\n')
		elif isinstance(v,dict) and not v:
			type_str=type_pre+'emptydict'
			value_str=value_pre+'empty'
			full_msg_str='%s\0%s\0%s'%(key_str,type_str,value_str)
			full_msg_str=full_msg_str.encode(encoding) if encoding else full_msg_str
			data_str.append(full_msg_str)
			if file:file.write(full_msg_str+'\n')
		elif isinstance(v,str) or isinstance(v,unicode):
			type_str=type_pre+'str'
			value_str=value_pre+v
			full_msg_str='%s\0%s\0%s'%(key_str,type_str,value_str)
			full_msg_str=full_msg_str.encode(encoding) if encoding else full_msg_str
			data_str.append(full_msg_str)
			if file:file.write(full_msg_str+'\n')
		elif isinstance(v,float):
			type_str=type_pre+'float'
			value_str=value_pre+'%.10e'%v
			full_msg_str='%s\0%s\0%s'%(key_str,type_str,value_str)
			full_msg_str=full_msg_str.encode(encoding) if encoding else full_msg_str
			data_str.append(full_msg_str)
			if file:file.write(full_msg_str+'\n')
		elif isinstance(v,int):
			type_str=type_pre+'int'
			value_str=value_pre+'%d'%v
			full_msg_str='%s\0%s\0%s'%(key_str,type_str,value_str)
			full_msg_str=full_msg_str.encode(encoding) if encoding else full_msg_str
			data_str.append(full_msg_str)
			if file:file.write(full_msg_str+'\n')
		elif isinstance(v,list) or (isinstance(v,tuple) and not isNamedTuple(v)):
			if len(v)==0:
				type_str=type_pre+'emptylist'
				value_str=value_pre+'empty'
				full_msg_str='%s\0%s\0%s'%(key_str,type_str,value_str)
				full_msg_str=full_msg_str.encode(encoding) if encoding else full_msg_str
				data_str.append(full_msg_str)
				if file:file.write(full_msg_str+'\n')
			elif v:
				v0=v[0]
				if isinstance(v0,str) or isinstance(v0,unicode):
					type_str=type_pre+'strlist'
					value_str=value_pre
					for s in v:
						value_str+='%s,'%s
					value_str=value_str[0:-1]
					full_msg_str='%s\0%s\0%s'%(key_str,type_str,value_str)
					full_msg_str=full_msg_str.encode(encoding) if encoding else full_msg_str
					data_str.append(full_msg_str)
					if file:file.write(full_msg_str+'\n')
				elif isinstance(v0,float):
					type_str=type_pre+'floatlist'
					value_str=value_pre
					for f in v:
						value_str+='%.10e,'%f
					value_str=value_str[0:-1]
					full_msg_str='%s\0%s\0%s'%(key_str,type_str,value_str)
					full_msg_str=full_msg_str.encode(encoding) if encoding else full_msg_str
					data_str.append(full_msg_str)
					if file:file.write(full_msg_str+'\n')
				elif isinstance(v0,int):
					type_str=type_pre+'intlist'
					value_str=value_pre
					for f in v:
						value_str+='%d,'%f
					value_str=value_str[0:-1]
					full_msg_str='%s\0%s\0%s'%(key_str,type_str,value_str)
					full_msg_str=full_msg_str.encode(encoding) if encoding else full_msg_str
					data_str.append(full_msg_str)
					if file:file.write(full_msg_str+'\n')
				elif isinstance(v0,list) or (isinstance(v0,tuple) and not isNamedTuple(v0)):
					celltype='vectorlist'
					for row in v:
						for cell in row:
							if isinstance(cell,str) or isinstance(cell,unicode):
								celltype='rowlist'
								break
					type_str=type_pre+celltype
					for vec in v:
						if vec:
							vec_str=''
							ty_str=''
							if celltype=='vectorlist':
								for f in vec: vec_str+='%.10e,'%f
								vec_str=vec_str[0:-1]
							else:
								# str function here returns a type string(type: str), but this string contains no non-ascii chars.
								# so it is safe to encode again
								for s in vec: 
									vec_str+='%s,'%s
									ty_str+='%s,'%str(type(s))
								vec_str=vec_str[0:-1]
								ty_str=ty_str[0:-1]
							value_str=value_pre+'%s'%vec_str
							full_msg_str='%s\0%s\0%s\0%s'%(key_str,type_str,value_str,ty_str)
							full_msg_str=full_msg_str.encode(encoding) if encoding else full_msg_str
							data_str.append(full_msg_str)
							if file:file.write(full_msg_str+'\n')
				elif isinstance(v0,dict):
					type_str=type_pre+'dictlist'
					for dic in v:
						if dic:
							# Create an dict_id to refer
							dict_id=''.join(random.sample(string.ascii_lowercase,4))
							# Append sub dict to the main dict
							data_str.extend(dict_strlist(dic,dict_id,encoding=encoding,file=file))
							
							value_str=value_pre+dict_id
							full_msg_str='%s\0%s\0%s'%(key_str,type_str,value_str)
							full_msg_str=full_msg_str.encode(encoding) if encoding else full_msg_str
							data_str.append(full_msg_str)
							if file:file.write(full_msg_str+'\n')
				elif isNamedTuple(v0):
					type_str=type_pre+'namedtuplelist'  # take as an OrderedDict
					TupleClass=GetNamedTupleClass(v0)
					for nd in v:
						dic=nd.__dict__     #this dict contains all fields
						if dic:
							dict_id=''.join(random.sample(string.ascii_lowercase,4))
							data_str.extend(dict_strlist(dic,dict_id,encoding=encoding,file=file))
							
							value_str=value_pre+dict_id
							full_msg_str='%s\0%s\0%s\0%s'%(key_str,type_str,value_str,TupleClass)
							full_msg_str=full_msg_str.encode(encoding) if encoding else full_msg_str
							data_str.append(full_msg_str)
							if file:file.write(full_msg_str+'\n')
		elif isNamedTuple(v):
			type_str=type_pre+'namedtuple'
			TupleClass=GetNamedTupleClass(v)
			dic=v.__dict__     #this dict contains all fields
			if dic:
				dict_id=''.join(random.sample(string.ascii_lowercase,4))
				data_str.extend(dict_strlist(dic,dict_id,encoding=encoding,file=file))
				
				value_str=value_pre+dict_id
				full_msg_str='%s\0%s\0%s\0%s'%(key_str,type_str,value_str,TupleClass)
				full_msg_str=full_msg_str.encode(encoding) if encoding else full_msg_str
				data_str.append(full_msg_str)
				if file:file.write(full_msg_str+'\n')
		
		if dialog and wx_imported:
			if signal.isSet():
				num+=1.0
				#print '%d   %d   %d'%(i,count,maximum)
				#wx.CallAfter(dialog.Update,int(num/count*maximum))
				wx.CallAfter(UpdateDialog,dialog,int(num/count*maximum*progress),signal)
			else:
				#wx.CallAfter(UpdateDialog,dialog,maximum,signal)
				return None
	
	return data_str

def UpdateDialog(dialog,i,event):
	res=dialog.Update(i)
	if not res[0]:event.clear()
	
def nextlevel(dic,p):
	path=[]
	if p:
		p+='.'
	for k in dic:
		v=dic[k]
		if isinstance(v,dict) and v:
			s=nextlevel(v,p+k)
			path.extend(s)
		else:
			path.append(p+k)
	return path

def isNamedTuple(t):
	if isinstance(t,tuple):
		if t.__class__==tuple:
			return False
		else:
			return True
	else:
		return False

def GetNamedTupleClass(t):
	if isNamedTuple(t):
		c='\''
		# str function here returns a type string(type: str), but this string contains no non-ascii chars. 
		# so the 'value' can be compared without coding problems
		s=str(t.__class__)
		index=[m.start() for m in re.finditer(c, s)]
		s=s[index[0]+1:index[1]]
		return s.split('.')[-1]
	else:
		return None

def strlist_dict(lines,decoding=None,dialog=None,progress=1):
	dic={}
	error_str='this is not a standard format for dict string.'
	if not lines or not isinstance(lines,list):
		raise NotDictStrError(error_str)

	num=0.
	count=len(lines)
	if dialog and wx_imported:
		signal = threading.Event()
		signal.set()
		dialog.Update(0)
		maximum=dialog.GetRange()
		
	for line in lines:
		line=line.rstrip()
		if decoding:line=line.decode(decoding)
		if line.find('\0')==-1:
			raise NotDictStrError(error_str)
		data=line.split('\0')
		key_str=data[0]
		type_str=data[1]
		value_str=data[2]
		addition=data[3] if len(data)>=4 else None
		if key_str.find('.')==-1:
			keypath=[key_str]
		else:
			keypath=key_str.split('.')
		v=dic
		for i in range(len(keypath)):
			if not v.has_key(keypath[i]):
				v[keypath[i]]=co.OrderedDict()
			if i!=len(keypath)-1:
				v=v[keypath[i]]
		k=keypath[-1]
		if type_str=='none' and value_str=='none':
			v[k]=None
		elif type_str=='emptydict' and value_str=='empty':
			v[k]={}
		elif type_str=='emptylist' and value_str=='empty':
			v[k]=[]
		elif type_str=='str':
			v[k]=value_str
		elif type_str=='float':
			v[k]=float(value_str)
		elif type_str=='int':
			v[k]=int(value_str)
		elif type_str=='strlist':
			v[k]=value_str.split(',')
		elif type_str=='floatlist':
			f=value_str.split(',')
			v[k]=[float(x) for x in f]
		elif type_str=='intlist':
			f=value_str.split(',')
			v[k]=[int(x) for x in f]
		elif type_str=='vectorlist':
			f=value_str.split(',')
			if not isinstance(v[k],list):
				v[k]=[]
			v[k].append([float(x) for x in f])
		elif type_str=='rowlist':
			s=value_str.split(',')
			ty_str=addition
			t=ty_str.split(',') if ty_str else None
			d=[ty(p) for p in zip(s,t)] if t else s
			if not isinstance(v[k],list):
				v[k]=[]
			v[k].append(d)
		elif type_str=='dictlist':
			d=dic.pop(value_str)
			if not isinstance(v[k],list):
				v[k]=[]
			v[k].append(d)
		elif type_str=='namedtuple':
			d=dic.pop(value_str)
			TupleClass=addition
			nd=BuildNamedTuple(d,TupleClass)
			v[k]=nd
		elif type_str=='namedtuplelist':
			d=dic.pop(value_str)
			TupleClass=addition
			nd=BuildNamedTuple(d,TupleClass)
			if not isinstance(v[k],list):
				v[k]=[]
			v[k].append(nd)

		if dialog and wx_imported:
			if signal.isSet():
				num+=1.0
				wx.CallAfter(UpdateDialog,dialog,int(num/count*maximum*progress),signal)
			else:
				return None

	return dic

def ty(p):
	if p and isinstance(p,tuple) and len(p)==2:
		value=p[0]
		ty=p[1]
		# str function here returns a type string(type: str), but this string contains no non-ascii chars. 
		# so the 'value' can be compared without coding problems
		if ty==str(str) or ty==str(unicode):
			return value
		elif ty==str(int):
			return int(value)
		elif ty==str(float):
			return float(value)
		else:
			return value
	else:
		return None

def BuildNamedTuple(dic,TupleClass):
	keys=(k for k in dic)
	nd=co.namedtuple(TupleClass,keys)
	t=nd._make([dic[k] for k in dic])
	return t
