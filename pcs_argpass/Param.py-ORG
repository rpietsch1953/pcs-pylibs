#!/usr/bin/env python3
'''
Parameterverwaltung
	bedient die meisten Laufzeitparameter
'''
import sys
import getopt
import types
import inspect
from pathlib import Path, PurePath
import json
import types


class Param(dict):
	'''
Main class and also the result-dictionary
normally imported as

from pcs_argpass.Param import Param
	'''
	class __ExceptionTemplate(Exception):
		def __call__(self, *args):
        		return self.__class__(*(self.args + args))

		def __str__(self):
        		return ': '.join(self.args)

	class DeclarationError(__ExceptionTemplate):
		'''
s exception is raised if there is an declaration error within the 
parameters of the class.
		'''
		pass
	class ParamError(__ExceptionTemplate):
		'''
s exception is raised if there is an error within the runtime-parameters.
s os only within the "Process"-function.
		'''
		pass
#---------------------------------------------
# Class-local Data
#---------------------------------------------
	__MyProgName = ""	# the programm-name from __Argumente[0] (only name)
	__MyProgPath = ""	# the path of the executeable from __Argumente[0]
	__MyPwd = ""		# Actual directory at invocation of "Process" 
	__Definition = {}	# the definition-dict
	__Description = ""	# Description of program for help
	__Argumente = []	# list of commandline arguments
	__ChkFunc = None	# external check-funktion (not implemented jet)
	__UsageText = ""	# Complete help-text
	__ShortList = ""	# String of short parameters (e.g. "vhl:m:")
	__LongList = []		# List of Long parameters (e.g. "help","len="...)
	__ParDict = {}		# dict of "argtext" -> "Parameter-name"
	__RemainArgs = []	# List of remaining arguments from commandline
	__AddPar = ""		# Additional parameter Text (for help)
	__UsageTextList = []	# List of single help entries (also lists)
	__IsPrepared = False	# Marker if "Prepare" is run after changes

	__HelpList = []		# List of all parameters with type 'H'
	__ImportList = []	# List of all parameters with type 'x'
	__ExportList = []	# List of all parameters with type 'X'
	__AllParams = True	# True if all parameters are initialized, if False
				# only parameters with defaults or on the commandline
				# are in the dictionary
	__DoTranslate = None	# Translation routine for error-messages'

	__WorkPars = {
		'shortpar':	's',
		'longpar':	'l', 
		'needoption':	'o', 
		'default':	'v',
		'mode':		'm',
		'description':	'd',
		'lowlimit':	'L', 
		'uplimit':	'U', 
		'required':	'r'
	}


	__WorkModes = {
		'text':		't', 
		'bool':		'b', 
		'path':		'p', 
		'file':		'f', 
		'dir':		'd', 
		'int':		'i', 
		'float':	'F', 
		'count':	'C',
		'help':		'H',
		'import':	'x',
		'export':	'X'
	}


	def __init__(	self, 
			Def: dict = {}, 
			Args: list = None, 
			Chk = None, 
			Desc: str = "", 
			AddPar: str = "", 
			AllParams: bool = True, 
			UserPars:dict = None, 
			UserModes: dict = None,
			Translate = None):
		""" The construktor
		Args:
		    Def (dict, optional): See SetDef(). Defaults to {}.
		    Args ([type], optional): See SetArgs(). Defaults to None.
		    Chk ([type], optional): See SetChk(). Defaults to None.
		    Desc (str, optional): See SetDesc(). Defaults to "".
		    AddPar (str, optional): See SetAddPar. Defaults to "".
		    AllParams (Boolean, optional): See SetAllParams. Defaults to True.
		    UserPars (dict, optional): See SetUserKeys. Defaults to None.
		    UserModes (dict, optional): See SetUserKeys. Defaults to None.
		"""
		super(Param, self).__init__()		# Init parent -> make me a dict
		# set the parameters with the individual functions
		self.SetDesc(Desc)
		self.SetUserKeys(UserPars = UserPars,UserModes = UserModes)
		self.SetDef(Def)
		self.SetArgs(Args)
		self.SetChk(Chk)
		self.SetAllParams(AllParams)
		self.SetAddPar(AddPar)
		self.SetTranslate(Translate)
		self.__IsPrepared = False

	def SetTranslate(self, Translate = None) -> None:
		""" Set translation routine for error-messages

		Args:
		    Translate (callable, optional): Defaults to None.
		    	example:
			    TransFunc(*,Type:str,Param:str, Path:str, FullPath:str, Msg:str, OptList:str) -> str:
			This function is called with the folowing parameters:
				Type, Param, Path, FullPath, Msg, OptList
			all of them are strings. The return value is the error-msg, also
			a string.
			The default messages are:
				if Type is "ImpFail"
					"Import failed, {Path} for parameter {Param} is not a valid file"
				if Type is "ErrMsg"
					"Error '{Msg}' in {Path} ({FullPath}) for parameter {Param}"
				if Type is "NoFile"
					"The path {Path} ({FullPath}) for parameter {Param} is not a file"
				if Type is "NoPath"
					"The path {Path} ({FullPath}) for parameter {Param} does not exist"
				if Type is "NoAct"
					"No action defined for {Param}"
				if Type is "Required"
					"{Param} ({OptList}) required but not given"
				for all other Type values
					"Undefined error Type='{Type}', Param='{Param}', Path='{Path}', FullPath='{FullPath}', Msg='{Msg}', OptList='{OptList}'"
			If this function is given it has to translate ALL messages.
			If an error occures, the default messages are used

		Raises:
		    self.DeclarationError: if Translate not callable or None
		"""
		if Translate is None:
			self.__DoTranslate = None
		else:
			if callable(Translate):
				self.__DoTranslate = Translate
			else:
				raise self.DeclarationError(f"Translate is not a function")

	def SetAllParams(self, AllParams: bool = True) -> None:
		""" Set the flag for All Params

		Args:
		    AllParams (bool, optional): If True, all params are initialized,
		    at least with None. If False params with no default and no setting on
		    the commandline are not defined within the dictionary. Defaults to True.
		"""		
		self.__AllParams = AllParams
		self.__IsPrepared = False	# we need a Prepare-call after this


	def SetDef(self, Def: dict = {}) -> None:
		"""
		Set the definition for processing arguments

		Args:
		    Def (dict, optional): A definition-dict. Defaults to {}.

		Raises:
		    TypeError: on error within the definition
		
		Describes the definition for arg-parsing.
		Def-dict: a dictionary of dictionaries
			{ 'Name1': {.. declaration ..}, 
			...
	  		'Name2': {.. declaration ..}, }
			"NameN" is the index under which at runtime you get the values 
				within the resulting dictionary.
			The individual definitions look like:
				{'s': 'a',
				'l': 'longval', 
				'o': True, 
				'v':"LuLu",
				'm': 't',
				'd': 'Description',
				'L': 'Low', 
				'U': 'Up', 
				'r': False },
			where:
				m : Mode -> 	t=Text, 
						b=Bool, 
						p=Path, 
						f=Existing File, 
						d=Exist. Dir, 
						i=Integer, 
						F=Float, 
						C=Counter (start default as 0 and increment each time found)
					The following are processed BEVOR all others:
						H=Show help and exit
						x=Import config-file as json (file must exist loke "f")
						can be given more than once!
					The following are processed AFTER all others:
						X=Export config as json to stdout und exit
				r : Required -> True or False, False is default
				s : Short Option(s) -> string or list or tuple of strings
				l : Long Option(s) -> string or list or tuple of strings
				o : Ein Parameter notendig -> True oder False, False is default
				v : Default value -> if not given: 
						"" for Text, 
						False for Bool, 
						None for Path, File and Dir,
						0 for Int und Counter, 
						0. for Float
				L : Lower Limit, value >= L if present
				U : Upper Limit, value <= U if present
				d : Description for helptext
			The entries "m" and ("s" or "l") must be present, all others are optional.		
		"""
		if type(Def) == dict:
			self.__Definition = Def
		else:
			raise TypeError('Def is not a dict')
		self.__IsPrepared = False	# we need a Prepare-call after this	


	def SetUserKeys(self, UserPars: dict = None, UserModes: dict = None) -> None:
		"""
		Set the key-table for the definition-dictionary

		Args:
		    UserPars (dict, optional): ignored if None. Defaults to None.
			Dictionary of keys used within the definition-dictionary.
			All key-value pairs are optional.
			Only the keys from self.__WorkPars are valid.
			The value has to be a string. This string replaces the 
			keysting for this key.
			After all changes are made the values within self.__WorkPars
			have to be unique!
		    UserModes (dict, optional): ignored if None. Defaults to None.
			Dictionary of modes used within the definition-dictionary.
			All key-value pairs are optional.
			Only the keys from self.__WorkModes are valid.
			The value has to be a string. This string replaces the 
			keysting for this key.
			After all changes are made the values within self.__WorkModes
			have to be unique!
		"""
		if UserPars is not None:
			if type(UserPars) != dict:
				raise TypeError('UserPars is not a dict')
			for k in UserPars.keys():
				if not k in self.__WorkPars:
					raise self.DeclarationError(f"UserPars {k} is invalid. Valid values are {self.__WorkPars.keys()}")
				v = UserPars[k]
				if type(v) != str:
					raise TypeError(f"Value of UserPars {k} is not a string")
				self.__WorkPars[k] = v
			Double = self.__CheckMulti(self.__WorkPars)
			if Double:
				raise self.DeclarationError(f"UserPars {Double} have the same value {self.__WorkPars[Double[0]]}")

		if UserModes is not None:
			if type(UserModes) != dict:
				raise TypeError('UserModes is not a dict')
			for k in UserModes.keys():
				if not k in self.__WorkModes:
					raise self.DeclarationError(f"UserModes {k} is invalid. Valid values are {self.__WorkModes.keys()}")
				v = UserModes[k]
				if type(v) != str:
					raise TypeError(f"Value of UserModes {k} is not a string")
				self.__WorkModes[k] = v
			Double = self.__CheckMulti(self.__WorkModes)
			if Double:
				raise self.DeclarationError(f"UserModes {Double} have the same value {self.__WorkModes[Double[0]]}")


	def __CheckMulti(self, Dict: dict) -> list:
		return [k for k,v in Dict.items() if list(Dict.values()).count(v)!=1]


	def SetArgs(self, Args: list = None) -> None:
		"""
		Set the argument list to process
		if None: use sys.argv as the arguments

		Args:
		    Args ([type], optional): Runtime Arguments. Defaults to None.

		Raises:
		    TypeError: If Args is not a list
		"""
		if Args is None:
			self.__Argumente = sys.argv
		elif type(Args) == list or type(Args) == tuple:
			self.__Argumente = Args
		else:
			raise TypeError('Args is not a list or tuple')


	def SetChk(self, Chk = None):
		"""
		Set the check-function. Not implementet now

		Args:
		    Chk ([type], optional): [description]. Defaults to None.

		Raises:
		    TypeError: if function is not of the proper type
		"""
		if Chk is None:
			self.__ChkFunc = Chk
		else:
			if isinstance(Chk, types.FunctionType):
				a = inspect.getfullargspec(Chk).args
				if len(a) != 2:
					raise TypeError('Check function does not take 2 arguments')
				self.__ChkFunc = Chk
			else:
				raise TypeError('Check is not a function')
		self.__IsPrepared = False	# we need a Prepare-call after this


	def SetDesc(self, Desc: str = "") -> None:
		"""
		Set the description of the program
		for usage-string

		Args:
		    Desc (str, optional): A descriptive string for the Program.
		    printed bevore the parameters. Defaults to "".

		Raises:
		    TypeError: if Desc is not a string.
		"""
		if type(Desc) == str:
			self.__Description = Desc
		else:
			raise TypeError('Desc is not a string')
		self.__IsPrepared = False	# we need a Prepare-call after this

	def SetAddPar(self, AddPar: str = "") -> None:
		"""
		Description of additional parameters for usage-function.
		printed in first line after "OPTIONS"

		Args:
		    AddPar (str, optional): The text or additional parameters. Defaults to "".

		Raises:
		    TypeError: if AddPar is not a string
		"""
		if type(AddPar) == str:
			self.__AddPar = AddPar
		else:
			raise TypeError('AddPar is not a string')
		self.__IsPrepared = False	# we need a Prepare-call after this

	def MyProgName(self) -> str:
		"""
		Return the program-name

		Returns:
		    str: Name of the executeable
		"""
		return self.__MyProgName

	def MyProgPath(self) -> str:
		"""
		Return the program-path

		Returns:
		    str: Path of the executeable
		"""
		return self.__MyProgPath

	def MyPwd(self) -> str:
		"""
		Return the directory at invocation of "Process"

		Returns:
		    str: Directory at "Process"-time
		"""
		return self.__MyPwd

	def __GenUsageText(self,ShortLen: int, LongLen: int) -> None:
		"""
		Generate the "Usage"-text

		Args:
		    ShortLen (int): Max. length of the "short"-options (0 or 1)
		    LongLen (int): Max. length of the "long"-options
		"""

		Text = f"Usage:\n{self.__MyProgName} OPTIONS {self.__AddPar}\n\n{self.__Description}\n\nOptions:\n"
		for Single in self.__UsageTextList:
			Ut_Short = Single[0]
			Ut_Long = Single[1]
			Ut_Param = Single[2]
			Ut_Type = Single[3]
			Ut_Default = Single[4]
			if Ut_Default is None or Ut_Default == '':
				Ut_Default = ""
			else:
				Ut_Default = f", Default: {str(Ut_Default)}"
			Ut_Text = Single[5].splitlines()
			sl = ShortLen + 3 + 1
			ll = LongLen + 3 + 2
			Lines = max(len(Ut_Short),len(Ut_Long),len(Ut_Text)+1)
			while len(Ut_Short) < Lines:
				Ut_Short.append(" ")
			
			while len(Ut_Long) < Lines:
				Ut_Long.append(" ")
			Ut_Text.insert(0,f"Type: {Ut_Type}{Ut_Default}")
			while len(Ut_Text) < Lines:
				Ut_Text.append(" ")
			
			for i in range(Lines):
				wLine = "\n   "
				s = Ut_Short[i]
				l = Ut_Long[i]
				t = Ut_Text[i]
				if s == " ":
					n = " " * sl
				else:
					n = ("-" + s + (" " * sl))[:sl]
				wLine += n
				if l == " ":
					n = " " * ll
				else:
					if Ut_Param.strip() == "":
						n = "--" + l
					else:
						n = "--" + l + "="
				if i == 0:
					n += Ut_Param.strip()
				n = (n + (" " * (ll + 4)))[:ll+4] 
				wLine += n + t
				Text += wLine
#			Text += "\n"
		self.__UsageText = Text

	def Usage(self) -> str:
		"""
		Return the helptext

		Returns:
		    str: The help-text
		"""
		if not self.__IsPrepared:
			self.__Prepare()
		return self.__UsageText

	def __Prepare(self) -> None:
		"""
		Prepare the class to be able to be used

		Raises:
		    self.DeclarationError: if there are errors within the declaration-dict
		"""

		# clear all values
		self.clear()
		self.__UsageText = ""
		LongParLen = 0	
		ShortParLen = 0
		self.__LongList = []
		self.__ShortList = ""
		self.__ParDict = {}
		self.__RemainArgs = []
		self.__UsageTextList = []
		self.__MyPwd = str(Path.cwd())
		self.__MyProgName = Path(sys.argv[0]).stem
		self.__MyProgPath = str(Path(sys.argv[0]).parent)

		for ParName in self.__Definition.keys():
			SingleDef = self.__Definition[ParName]
			Ut_Short = []
			Ut_Long = []
			Ut_Param = ""
			Ut_Default = ""
			Ut_Text = ""
			Ut_Type = ""
			ParKeys = SingleDef.keys()
			if self.__WorkPars['mode'] in ParKeys:
				ParMode = SingleDef[self.__WorkPars['mode']]
			else:
				raise self.DeclarationError(f"No mode setting in Def for {ParName}")
			if ParMode == self.__WorkModes['path']:
				Ut_Type = 'path'
				SingleDef[self.__WorkPars['needoption']] = True
			elif ParMode == self.__WorkModes['int']:
				Ut_Type = 'integer'
				Ut_Default = 0
			elif ParMode == self.__WorkModes['bool']:
				Ut_Type = 'boolean'
				Ut_Default = False
			elif ParMode == self.__WorkModes['float']:
				Ut_Type = 'float'
				Ut_Default = 0.0
			elif ParMode == self.__WorkModes['file']:
				Ut_Type = 'file'
				SingleDef[self.__WorkPars['needoption']] = True
			elif ParMode == self.__WorkPars['description']:
				Ut_Type = 'directory'
				SingleDef[self.__WorkPars['needoption']] = True
			elif ParMode == self.__WorkModes['count']:
				Ut_Type = 'counter'
			elif ParMode == self.__WorkModes['help']:
				Ut_Type = 'help'
			elif ParMode == self.__WorkModes['import']:
				Ut_Type = 'import'
				SingleDef[self.__WorkPars['needoption']] = True
			elif ParMode == self.__WorkModes['export']:
				Ut_Type = 'export'
			else:
				Ut_Type = 'string'

			if self.__WorkPars['default'] in ParKeys:
				if 	SingleDef[self.__WorkPars['mode']] != self.__WorkModes['help'] \
					and SingleDef[self.__WorkPars['mode']] != self.__WorkModes['import'] \
					and SingleDef[self.__WorkPars['mode']] != self.__WorkModes['export']:
					self[ParName] = SingleDef[self.__WorkPars['default']]
				if ParMode == self.__WorkModes['file']:
					wText = SingleDef[self.__WorkPars['default']]
					try:
						if wText[0] != "/":
							wText = self.__MyPwd + '/' + wText
						wFile = Path(wText).absolute()
						if wFile.is_file:
							self[ParName] = str(wFile)
					except:
						wText = ''
						self[ParName] = wText
				elif ParMode == self.__WorkPars['description']:
					wText = SingleDef[self.__WorkPars['default']]
					if wText[0] != "/":
						wText = self.__MyPwd + '/' + wText
					wFile = Path(wText).absolute()
					if wFile.is_dir:
						self[ParName] = str(wFile)
				elif ParMode == self.__WorkModes['path']:
					wText = SingleDef[self.__WorkPars['default']]
					if wText[0] != "/":
						wText = self.__MyPwd + '/' + wText
					wFile = Path(wText).absolute()
					self[ParName] = str(wFile)
				Ut_Default = SingleDef[self.__WorkPars['default']]
			else:
				if self.__AllParams:
					if ParMode == self.__WorkModes['bool']:
						self[ParName] = False
					elif ParMode == self.__WorkModes['text']:
						self[ParName] = ""
					elif ParMode == self.__WorkModes['int']:
						self[ParName] = 0
					elif ParMode == self.__WorkModes['float']:
						self[ParName] = 0.
					elif ParMode == self.__WorkModes['count']:
						self[ParName] = 0
					else:
						if ParMode not in "xXH":
							self[ParName] = None
			NeedOpt = False
			if self.__WorkPars['needoption'] in ParKeys:
				if SingleDef[self.__WorkPars['needoption']]:
					NeedOpt = True
					Ut_Param = 'XXX'
			if self.__WorkPars['longpar'] in ParKeys:
				wText = SingleDef[self.__WorkPars['longpar']]
				if type(wText) == list or type(wText) == tuple:
					for ws in wText:
						if not type(ws) == str:
							raise self.DeclarationError(f"One of the long values for {ParName} is not a string")
						l = len(ws)
						if ('--' + ws) in self.__ParDict.keys():
							raise self.DeclarationError(f"Double long value for {ParName}: {ws}")
						self.__ParDict['--' + ws] = ParName
						if ParMode == self.__WorkModes['help']:
							self.__HelpList.append('--' + ws)
						elif ParMode == self.__WorkModes['import']:
							self.__ImportList.append('--' + ws)
						elif ParMode == self.__WorkModes['export']:
							self.__ExportList.append('--' + ws)
						Ut_Long.append(ws)
						if NeedOpt:
							self.__LongList.append(ws + "=")
						else:
							self.__LongList.append(ws)
						if l > LongParLen:
							LongParLen = l
				elif not type(wText) == str:
					raise self.DeclarationError(f"Long value for {ParName} is not a string")
				else:
					if ('--' + wText) in self.__ParDict.keys():
						raise self.DeclarationError(f"Double long value for {ParName}: {wText}")
					self.__ParDict['--' + wText] = ParName
					if ParMode == self.__WorkModes['help']:
						self.__HelpList.append('--' + wText)
					elif ParMode == self.__WorkModes['import']:
						self.__ImportList.append('--' + wText)
					elif ParMode == self.__WorkModes['export']:
						self.__ExportList.append('--' + wText)
					Ut_Long.append(wText)
					l = len(wText)
					if NeedOpt:
						self.__LongList.append(wText + "=")
					else:
						self.__LongList.append(wText)
					if l > LongParLen:
						LongParLen = l
			if self.__WorkPars['shortpar'] in ParKeys:
				wText = SingleDef[self.__WorkPars['shortpar']]
				if type(wText) == list or type(wText) == tuple:
					for ws in wText:
						if not type(ws) == str:
								raise self.DeclarationError(f"One of the short values for {ParName} is not a string")
						for c in ws:
							if ('-' + c) in self.__ParDict.keys():
								raise self.DeclarationError(f"Double short value for {ParName}: {c}")
							self.__ParDict['-' + c] = ParName
							if ParMode == self.__WorkModes['help']:
								self.__HelpList.append('-' + c)
							elif ParMode == self.__WorkModes['import']:
								self.__ImportList.append('-' + c)
							elif ParMode == self.__WorkModes['export']:
								self.__ExportList.append('-' + c)
							Ut_Short.append(c)
							self.__ShortList += c
							if NeedOpt:
								self.__ShortList += ":"
				elif not type(wText) == str:
					raise self.DeclarationError(f"Short value for {ParName} is not a string")
				else:
					for c in wText:
						if ('-' + c) in self.__ParDict.keys():
							raise self.DeclarationError(f"Double short value for {ParName}: {c}")
						self.__ParDict['-' + c] = ParName
						if ParMode == self.__WorkModes['help']:
							self.__HelpList.append('-' + c)
						elif ParMode == self.__WorkModes['import']:
							self.__ImportList.append('-' + c)
						elif ParMode == self.__WorkModes['export']:
							self.__ExportList.append('-' + c)
						Ut_Short.append(c)
						self.__ShortList += c
						if NeedOpt:
							self.__ShortList += ":"
				if ShortParLen == 0:
					ShortParLen = 1
			if self.__WorkPars['description'] in ParKeys:
				Ut_Text = SingleDef[self.__WorkPars['description']]
			self.__UsageTextList.append( [Ut_Short,Ut_Long,Ut_Param,Ut_Type,Ut_Default,Ut_Text] )
		self.__GenUsageText(ShortParLen,LongParLen)
		self.__IsPrepared = True


	def __MakeErrorMsg(self, Type=None, Param="", Path="", FullPath = "", Msg = "", OptList = "") -> str:
		try:
			Erg = self.__DoTranslate(Type=Type, Param=Param, Path=Path, FullPath = FullPath, Msg = Msg, OptList = OptList)
			if type(Erg) == str:
				return Erg
		except:
			pass

		if Type == "ImpFail":
			return f"Import failed, {Path} for parameter {Param} is not a valid file"
		if Type == "ErrMsg":
			return f"Error '{Msg}' in {Path} ({FullPath}) for parameter {Param}"
		if Type == "NoFile":
			return f"The path {Path} ({FullPath}) for parameter {Param} is not a file"
		if Type == "NoPath":
			return f"The path {Path} ({FullPath}) for parameter {Param} does not exist"
		if Type == "NoAct":
			return f"No action defined for {Param}"
		if Type == "Required":
			return f"{Param} ({OptList}) required but not given"
		return f"Undefined error Type='{Type}', Param='{Param}', Path='{Path}', FullPath='{FullPath}', Msg='{Msg}', OptList='{OptList}'"



	def Process(self) -> None:
		"""
		Process the runtime-arguments

		Raises:
		    self.ParamError: if an error occures within a parameter
		    RuntimeError: if an internal error occures
		"""
		if not self.__IsPrepared:
			self.__Prepare()
		try:
			opts, args = getopt.getopt(self.__Argumente[1:],self.__ShortList,self.__LongList)
		except getopt.GetoptError as exc:
			wMsg = exc.msg
			raise self.ParamError(wMsg) from None
		self.__RemainArgs = args
		for o, a in opts:
			if o in self.__HelpList:
				print(self.Usage())
				sys.exit(0)

		for o, a in opts:
			if o in self.__ImportList:
				try:
					n = Path(a).resolve()
				except:
					raise self.ParamError(self.__MakeErrorMsg(Type="ImpFail",Path=a,Param=o)) from None
				if n.exists():
					if n.is_file():
						try:
							wDict = json.load(n.open())
						except Exception as exc:
							wMsg = str(exc)
							raise self.ParamError(self.__MakeErrorMsg(Type="ErrMsg",Msg=wMsg,Path=a,FullPath=n,Param=o)) from None
						for k in self.keys():
							try:
								self[k] = wDict[k]
							except:
								pass
					else:
						raise self.ParamError(self.__MakeErrorMsg(Type="NoFile",Path=a,FullPath=n,Param=o)) from None
				else:
					raise self.ParamError(self.__MakeErrorMsg(Type="NoPath",Path=a,FullPath=n,Param=o)) from None

		for o, a in opts:
			if o in self.__HelpList:
				continue
			if o in self.__ImportList:
				continue
			if o in self.__ExportList:
				continue
			try:
				ParName = self.__ParDict[o] 
			except:
				raise RuntimeError("Internal error, option {o} not found in ParDict")
			try:
				wPar = self.__Definition[ParName]
			except:
				raise RuntimeError("Internal error, option {ParName} not found in Definition")
			if self.__WorkPars['needoption'] in wPar.keys():
				if wPar[self.__WorkPars['needoption']]:
					Res = self.__CheckOption(ParName,o,wPar,a)
					if not Res is None:
						raise self.ParamError(Res)
					continue
			if wPar[self.__WorkPars['mode']] == self.__WorkModes['bool']:
				try:
					bVal = wPar[self.__WorkPars['default']]
				except:
					bVal = False
				self[ParName] = not bVal
			elif wPar[self.__WorkPars['mode']] == self.__WorkModes['count']:
				self[ParName] += 1
			else:
				raise self.ParamError(self.__MakeErrorMsg(Type="NoAct",Param=ParName))

		for o, a in opts:
			if o in self.__ExportList:
				print(json.dumps(self, sort_keys=True, indent=4))
				sys.exit(0)

		for i in self.__Definition.keys():
			v = self.__Definition[i]
			Req = False
			if self.__WorkPars['required'] in v.keys():
				Req = v[self.__WorkPars['required']]
			if Req:
				if not i in self.keys():
					raise self.ParamError(self.__MakeErrorMsg(Type="Required",Param=i,OptList=self.__GetOptList(i))) from None

	def __GetOptList(self,Name: str) -> str:
		""" liste der möglichen Parameter eines Keys"""
		w = self.__Definition[Name]
		Erg = ""
		if self.__WorkPars['shortpar'] in w.keys():
			Short = w[self.__WorkPars['shortpar']]
			if type(Short) == str:
				for s in Short:
					Erg += ('-' + s + ' ')
			else:
				for n in Short:
					for s in n:
						Erg += ('-' + s + ' ')
		if self.__WorkPars['longpar'] in w.keys():
			Long = w[self.__WorkPars['longpar']]
			Erg += ('--' + Long + ' ')
		return Erg

	def __CheckOption(self, ParName: str, ParKey: str, wPar: dict, a: str):
		"""[summary]

		Args:
		    ParName (string): Name of the parameter (index in class as dictionary)
		    ParKey (string): The parameter-value from commandline
		    wPar (dict): The definition dictionary for this parameter
		    a (string): the option given for this parameter

		Returns:
		    None	if no error
		    Error-msg	if option is erroneous
		"""
		wMod = wPar[self.__WorkPars['mode']]
#-------------------------
# Text
#-------------------------
		if wMod == self.__WorkModes['text']:
			try:
				ll = wPar[self.__WorkPars['lowlimit']]
				if a < ll:
					return f"Value {a} for parameter {ParKey} is less than lower limit ({ll})"
			except:
				pass
			try:
				ul = wPar[self.__WorkPars['uplimit']]
				if a > ul:
					return f"Value {a} for parameter {ParKey} is bigger than upper limit ({ul})"
			except:
				pass
			self[ParName] = a
			return None
#-------------------------
# Integer
#-------------------------
		if wMod == self.__WorkModes['int']:
			try:
				n = int(a)
			except:
				return f"Value {a} for parameter {ParKey} is not an integer"
			try:
				ll = wPar[self.__WorkPars['lowlimit']]
				if n < ll:
					return f"Value {a} for parameter {ParKey} is less than lower limit ({ll})"
			except:
				pass
			try:
				ul = wPar[self.__WorkPars['uplimit']]
				if n > ul:
					return f"Value {a} for parameter {ParKey} is bigger than upper limit ({ul})"
			except:
				pass
			self[ParName] = n
			return None
#-------------------------
# Float
#-------------------------
		if wMod == self.__WorkModes['float']:
			try:
				n = float(a)
			except:
				return f"Value {a} for parameter {ParKey} is not floating point"
			try:
				ll = wPar[self.__WorkPars['lowlimit']]
				if n < ll:
					return f"Value {a} for parameter {ParKey} is less than lower limit ({ll})"
			except:
				pass
			try:
				ul = wPar[self.__WorkPars['uplimit']]
				if n > ul:
					return f"Value {a} for parameter {ParKey} is bigger than upper limit ({ul})"
			except:
				pass
			self[ParName] = n
			return None
#-------------------------
# Boolean
#-------------------------
		if wMod == self.__WorkModes['bool']:
			try:
				n = a.lower()[0]
			except:
				return f"Value {a} for parameter {ParKey} is not valid"
			if n in 'jyt1':
				self[ParName] = True
				return None
			if n in 'n0':
				self[ParName] = False
				return None
			return f"Value {a} for parameter {ParKey} is not valid"
#-------------------------
# File (existing)
#-------------------------
		if wMod == self.__WorkModes['file']:
			if a[0] != "/":
				a = self.__MyPwd + "/" + a
			try:
				n = Path(a).resolve()
			except:
				return f"The name {a} for parameter {ParKey} is not a valid path"
			if n.exists():
				if n.is_file():
					self[ParName] = str(n)
					return None
				else:
					return f"The path {a} ({n}) for parameter {ParKey} is not a file"
			return f"The path {a} ({n}) for parameter {ParKey} does not exist"
#-------------------------
# Directory (existing)
#-------------------------
		if wMod == self.__WorkModes['dir']:
			if a[0] != "/":
				a = self.__MyPwd + "/" + a
			try:
				n = Path(a).resolve()
			except:
				return f"The name {a} for parameter {ParKey} is not a valid path"
			if n.exists():
				if n.is_dir():
					self[ParName] = str(n)
					return None
				else:
					return f"The path {a} ({n}) for parameter {ParKey} is not a directory"
			return f"The path {a} ({n}) for parameter {ParKey} does not exist"
#-------------------------
# Path
#-------------------------
		if wMod == self.__WorkModes['path']:
			if a[0] != "/":
				a = self.__MyPwd + "/" + a
			try:
				n = Path(a).resolve()
			except:
				return f"The name {a} for parameter {ParKey} is not a valid path"
			self[ParName] = str(n)
			return None
		
		return None

	def GetRemainder(self) -> list:
		"""
		Return list of additionel arguments on command-line

		Returns:
		    list: List of additional arguments within runtime-arguments
		"""
		return self.__RemainArgs

	def GetLongOpts(self) -> list:
		"""
		Return list of long options
		(only? for debugging declarations)

		Returns:
		    list: List of long options
		"""
		return self.__LongList

	def GetShortOpts(self) -> list:
		"""
		Return list of short options
		(only? for debugging declarations)

		Returns:
		    str: List of short options
		"""
		return self.__ShortList		
	
	def GetParDict(self) -> dict:
		"""
		Return dict with references options -> parameter-names
		(only? for debugging declarations)

		Returns:
		    dict: {option: name, ...}
		"""
		return self.__ParDict




TestDef_1 = 	{
	'Help': {	's': 'h',
			'l': 'help',
			'm': 'H',
			'd': 'Diesen Hilfetext anzeigen und beenden'},
	'Export': {	's': 'x',
			'l': 'export',
			'm': 'X',
			'd': 'Ausgabe der aktuellen Konfiguration und Beenden'},
	'ConfFile': {	's': 'z',
			'l': 'par',
			'm': 'x',
			'd': '''Zuerst die Werte aus der Datei lesen, 
danach erst die Komandozeilenparameter'''},
	'Verbose': {	's': 'v',
			'l': 'verbose',
			'r': False,
			'm': 'b',
			'd': 'Sei gesprächig'},
	'Count': {	's': 'c',
			'l': ('count','Count'),
			'r': True,
			'o': True,
			'v': 7,
			'm': 'i',
			'L': 1,
			'U': 10,
			'd': 'Eine Zahl zwischen 1 und 10'},
	'Float': {	's': 'F',
			'l': ('float','Float'),
			'o': True,
			'v': 10.47,
			'm': 'F',
			'L': 1,
			'U': 100.2,
			'd': 'Eine Gleitkommazahl zwischen 1 und 100.2'},
	'File': {	's': 'f',
			'l': 'file',
			'o': True,
			'm': 'f',
			'd': 'Eine existierende Datei'},
	'Dir': {	's': 'd',
			'l': 'dir',
			'o': True,
			'm': 'd',
			'd': 'Ein existierendes Verzeichnis'},
	'Path': {	's': 'p',
			'l': 'path',
			'r': 'true',
			'o': True,
			'm': 'p',
			'd': 'Ein gültiger Path'},
	'Counter': {	's': 'C',
			'o': False,
			'm': 'C',
			'd': 'Mehrmals zum hochzählen'},
	}


import shlex

def Trans(*,Type:str,Param:str, Path:str, FullPath:str, Msg:str, OptList:str) -> str:
	if Type == "ImpFail":
		return f"Fehler bei Import: {Path} bei Parameter {Param} ist keine gültige Datei"
	if Type == "ErrMsg":
		return f"Fehler '{Msg}' betreffend Datei {Path} ({FullPath}) von Parameter {Param}"
	if Type == "NoFile":
		return f"Der Pfad {Path} ({FullPath}) für Parameter {Param} ist keine Datei"
	if Type == "NoPath":
		return f"Der Pfad {Path} ({FullPath}) für Parameter {Param} existiert nicht"
	if Type == "NoAct":
		return f"Kein Inhalt für den Parameter {Param} angegeben"
	if Type == "Required":
		return f"Der Parameter {Param} ({OptList}) muss angegeben werden, ist aber nicht vorhanden"
	return f"Unbekannter Fehler Type='{Type}', Param='{Param}', Path='{Path}', FullPath='{FullPath}', Msg='{Msg}', OptList='{OptList}'"


def main():
	a = Param(Def = TestDef_1, 
		Desc = "Dies ist ein Test\ndas bedeutet hier steht nur\nnonsens", 
		AddPar = "File .... File", 
		Translate = Trans,
		AllParams = False,
		)
	# a.SetArgs(Args = shlex.split('Test -v -CCC -f /Mist --dir=/tmp'))
	try:
		a.Process()
	except Exception as exc:
		dir(exc)
		print(exc)
		return
	for key,value in a.items():
		print(key,value)
	# print(dir(a))
	print(f"Ergebnis: {a}")
	print(f"Rest: {a.GetRemainder()}")
	# print(a.Usage())
	
if __name__ == "__main__":
	main()
