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



class Param(dict):
	'''
Hauptklasse und gleichzeitig das Ergebnis-Dictionary
wird normalerweise mit

from parameter import Param

eingebunden.
	'''
	class __ExceptionTemplate(Exception):
		def __call__(self, *args):
        		return self.__class__(*(self.args + args))

		def __str__(self):
        		return ': '.join(self.args)

	class DeclarationError(__ExceptionTemplate):
		'''
Diese Exception wird ausgelöst wenn in der Deklaration
ein Fehler vorliegt.
Dies ist im Konstructor oder den "SetXXX" Funktionen
sowie in der "Process" Funktion  möglich.
		'''
		pass
	class ParamError(__ExceptionTemplate):
		'''
Diese Exception wird ausgelöst wenn in fehler in den
Laufzeitargumenten vorliegt.
Dies ist in der "Process" Funktion möglich.
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
	__AllParams = True

	def __init__(self, Def = {}, Args = None, Chk = None, Desc = "", AddPar = "", AllParams = True):
		""" The construktor
		Args:
		    Def (dict, optional): See SetDef(). Defaults to {}.
		    Args ([type], optional): See SetArgs(). Defaults to None.
		    Chk ([type], optional): See SetChk(). Defaults to None.
		    Desc (str, optional): See SetDesc(). Defaults to "".
		    AddPar (str, optional): See SetAddPar. Defaults to "".
		    AllParams (Boolean, optional): See SetAllParams. Defaults to True.
		"""
		super(Param, self).__init__()		# Init parent -> make me a dict
		# set the parameters with the individual functions
		self.SetDesc(Desc)
		self.SetDef(Def)
		self.SetArgs(Args)
		self.SetChk(Chk)
		self.SetAllParams(AllParams)
		self.SetAddPar(AddPar)
		self.__IsPrepared = False


	def SetAllParams(self, AllParams = True):
		""" Set the flag for All Params

		Args:
		    AllParams (bool, optional): If True, all params are initialized,
		    at least with None. If False params with no default and no setting on
		    the commandline are not defined within the dictionary. Defaults to True.
		"""		
		self.__AllParams = AllParams
		self.__IsPrepared = False	# we need a Prepare-call after this


	def SetDef(self, Def = {}):
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

	def SetArgs(self, Args=None):
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

	def SetDesc(self, Desc = ""):
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

	def SetAddPar(self, AddPar = ""):
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

	def MyProgName(self):
		"""
		Return the program-name

		Returns:
		    str: Name of the executeable
		"""
		return self.__MyProgName

	def MyProgPath(self):
		"""
		Return the program-path

		Returns:
		    str: Path of the executeable
		"""
		return self.__MyProgPath

	def MyPwd(self):
		"""
		Return the directory at invocation of "Process"

		Returns:
		    str: Directory at "Process"-time
		"""
		return self.__MyPwd

	def __GenUsageText(self,ShortLen,LongLen):
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

	def Usage(self):
		"""
		Return the helptext

		Returns:
		    str: The help-text
		"""
		if not self.__IsPrepared:
			self.__Prepare()
		return self.__UsageText

	def __Prepare(self):
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
			if 'm' in ParKeys:
				ParMode = SingleDef['m']
			else:
				raise self.DeclarationError(f"No mode setting in Def for {ParName}")
			if ParMode == 'p':
				Ut_Type = 'path'
				SingleDef['o'] = True
			elif ParMode == 'i':
				Ut_Type = 'integer'
				Ut_Default = 0
			elif ParMode == 'b':
				Ut_Type = 'boolean'
				Ut_Default = False
			elif ParMode == 'F':
				Ut_Type = 'float'
				Ut_Default = 0.0
			elif ParMode == 'f':
				Ut_Type = 'file'
				SingleDef['o'] = True
			elif ParMode == 'd':
				Ut_Type = 'directory'
				SingleDef['o'] = True
			elif ParMode == 'C':
				Ut_Type = 'counter'
			elif ParMode == 'H':
				Ut_Type = 'help'
			elif ParMode == 'x':
				Ut_Type = 'import'
				SingleDef['o'] = True
			elif ParMode == 'X':
				Ut_Type = 'export'
			else:
				Ut_Type = 'string'

			if 'v' in ParKeys:
				if SingleDef['m'] not in "xXH":
					self[ParName] = SingleDef['v']
				if ParMode == 'f':
					wText = SingleDef['v']
					if wText[0] != "/":
						wText = self.__MyPwd + '/' + wText
					wFile = Path(wText).absolute()
					if wFile.is_file:
						self[ParName] = str(wFile)
				elif ParMode == 'd':
					wText = SingleDef['v']
					if wText[0] != "/":
						wText = self.__MyPwd + '/' + wText
					wFile = Path(wText).absolute()
					if wFile.is_dir:
						self[ParName] = str(wFile)
				elif ParMode == 'p':
					wText = SingleDef['v']
					if wText[0] != "/":
						wText = self.__MyPwd + '/' + wText
					wFile = Path(wText).absolute()
					self[ParName] = str(wFile)
				Ut_Default = SingleDef['v']
			else:
				if self.__AllParams:
					if ParMode == 'b':
						self[ParName] = False
					elif ParMode == 't':
						self[ParName] = ""
					elif ParMode == 'i':
						self[ParName] = 0
					elif ParMode == 'F':
						self[ParName] = 0.
					elif ParMode == 'C':
						self[ParName] = 0
					else:
						if ParMode not in "xXH":
							self[ParName] = None
			NeedOpt = False
			if 'o' in ParKeys:
				if SingleDef['o']:
					NeedOpt = True
					Ut_Param = 'XXX'
			if 'l' in ParKeys:
				wText = SingleDef['l']
				if type(wText) == list or type(wText) == tuple:
					for ws in wText:
						if not type(ws) == str:
							raise self.DeclarationError(f"One of the long values for {ParName} is not a string")
						l = len(ws)
						if ('--' + ws) in self.__ParDict.keys():
							raise self.DeclarationError(f"Double long value for {ParName}: {ws}")
						self.__ParDict['--' + ws] = ParName
						if ParMode == 'H':
							self.__HelpList.append('--' + ws)
						elif ParMode == 'x':
							self.__ImportList.append('--' + ws)
						elif ParMode == 'X':
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
					if ParMode == 'H':
						self.__HelpList.append('--' + wText)
					elif ParMode == 'x':
						self.__ImportList.append('--' + wText)
					elif ParMode == 'X':
						self.__ExportList.append('--' + wText)
					Ut_Long.append(wText)
					l = len(wText)
					if NeedOpt:
						self.__LongList.append(wText + "=")
					else:
						self.__LongList.append(wText)
					if l > LongParLen:
						LongParLen = l
			if 's' in ParKeys:
				wText = SingleDef['s']
				if type(wText) == list or type(wText) == tuple:
					for ws in wText:
						if not type(ws) == str:
								raise self.DeclarationError(f"One of the short values for {ParName} is not a string")
						for c in ws:
							if ('-' + c) in self.__ParDict.keys():
								raise self.DeclarationError(f"Double short value for {ParName}: {c}")
							self.__ParDict['-' + c] = ParName
							if ParMode == 'H':
								self.__HelpList.append('-' + c)
							elif ParMode == 'x':
								self.__ImportList.append('-' + c)
							elif ParMode == 'X':
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
						if ParMode == 'H':
							self.__HelpList.append('-' + c)
						elif ParMode == 'x':
							self.__ImportList.append('-' + c)
						elif ParMode == 'X':
							self.__ExportList.append('-' + c)
						Ut_Short.append(c)
						self.__ShortList += c
						if NeedOpt:
							self.__ShortList += ":"
				if ShortParLen == 0:
					ShortParLen = 1
			if 'd' in ParKeys:
				Ut_Text = SingleDef['d']
			self.__UsageTextList.append( [Ut_Short,Ut_Long,Ut_Param,Ut_Type,Ut_Default,Ut_Text] )
		self.__GenUsageText(ShortParLen,LongParLen)
		self.__IsPrepared = True

	def Process(self):
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
					raise self.ParamError(f"The name {a} for parameter {o} is not a valid path") from None
				if n.exists():
					if n.is_file():
						try:
							wDict = json.load(n.open())
						except Exception as exc:
							wMsg = str(exc)
							raise self.ParamError(f"Error '{str(wMsg)}' in {a} ({n}) for parameter {o}") from None
						for k in self.keys():
							try:
								self[k] = wDict[k]
							except:
								pass
					else:
						raise self.ParamError(f"The path {a} ({n}) for parameter {o} is not a file") from None
				else:
					raise self.ParamError(f"The path {a} ({n}) for parameter {o} does not exist") from None

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
			if 'o' in wPar.keys():
				if wPar['o']:
					Res = self.__CheckOption(ParName,o,wPar,a)
					if not Res is None:
						raise self.ParamError(Res)
					continue
			if wPar['m'] == 'b':
				try:
					bVal = wPar['v']
				except:
					bVal = False
				self[ParName] = not bVal
			elif wPar['m'] == 'C':
				self[ParName] += 1
			else:
				raise self.ParamError(f"No action defined for {ParName}")

		for o, a in opts:
			if o in self.__ExportList:
				print(json.dumps(self, sort_keys=True, indent=4))
				sys.exit(0)

		for i in self.__Definition.keys():
			v = self.__Definition[i]
			Req = False
			if 'r' in v.keys():
				Req = v['r']
			if Req:
				if not i in self.keys():
					raise self.ParamError(f"{i} ({self.__GetOptList(i)}) required but not given")

	def __GetOptList(self,Name):
		""" liste der möglichen Parameter eines Keys"""
		w = self.__Definition[Name]
		Erg = ""
		if 's' in w.keys():
			Short = w['s']
			if type(Short) == str:
				for s in Short:
					Erg += ('-' + s + ' ')
			else:
				for n in Short:
					for s in n:
						Erg += ('-' + s + ' ')
		if 'l' in w.keys():
			Long = w['l']
			Erg += ('--' + Long + ' ')
		return Erg

	def __CheckOption(self,ParName,ParKey,wPar,a):
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
		wMod = wPar['m']
#-------------------------
# Text
#-------------------------
		if wMod == 't':
			try:
				ll = wPar['L']
				if a < ll:
					return f"Value {a} for parameter {ParKey} is less than lower limit ({ll})"
			except:
				pass
			try:
				ul = wPar['U']
				if a > ul:
					return f"Value {a} for parameter {ParKey} is bigger than upper limit ({ul})"
			except:
				pass
			self[ParName] = a
			return None
#-------------------------
# Integer
#-------------------------
		if wMod == 'i':
			try:
				n = int(a)
			except:
				return f"Value {a} for parameter {ParKey} is not an integer"
			try:
				ll = wPar['L']
				if n < ll:
					return f"Value {a} for parameter {ParKey} is less than lower limit ({ll})"
			except:
				pass
			try:
				ul = wPar['U']
				if n > ul:
					return f"Value {a} for parameter {ParKey} is bigger than upper limit ({ul})"
			except:
				pass
			self[ParName] = n
			return None
#-------------------------
# Float
#-------------------------
		if wMod == 'F':
			try:
				n = float(a)
			except:
				return f"Value {a} for parameter {ParKey} is not floating point"
			try:
				ll = wPar['L']
				if n < ll:
					return f"Value {a} for parameter {ParKey} is less than lower limit ({ll})"
			except:
				pass
			try:
				ul = wPar['U']
				if n > ul:
					return f"Value {a} for parameter {ParKey} is bigger than upper limit ({ul})"
			except:
				pass
			self[ParName] = n
			return None
#-------------------------
# Boolean
#-------------------------
		if wMod == 'b':
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
		if wMod == 'f':
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
		if wMod == 'd':
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
		if wMod == 'p':
			if a[0] != "/":
				a = self.__MyPwd + "/" + a
			try:
				n = Path(a).resolve()
			except:
				return f"The name {a} for parameter {ParKey} is not a valid path"
			self[ParName] = str(n)
			return None
		
		return None

	def GetRemainder(self):
		"""
		Return list of additionel arguments on command-line

		Returns:
		    list: List of additional arguments within runtime-arguments
		"""
		return self.__RemainArgs

	def GetLongOpts(self):
		"""
		Return list of long options
		(only? for debugging declarations)

		Returns:
		    list: List of long options
		"""
		return self.__LongList

	def GetShortOpts(self):
		"""
		Return list of short options
		(only? for debugging declarations)

		Returns:
		    str: List of short options
		"""
		return self.__ShortList		
	
	def GetParDict(self):
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
def main():
	a = Param(Def = TestDef_1, Desc = "Dies ist ein Test\ndas bedeutet hier steht nur\nnonsens", AddPar = "File .... File", AllParams = False)
	# a.SetArgs(Args = shlex.split('Test -v -CCC -f /Mist --dir=/tmp'))
	a.Process()
	for key,value in a.items():
		print(key,value)
	# print(dir(a))
	print(f"Ergebnis: {a}")
	print(f"Rest: {a.GetRemainder()}")
	# print(a.Usage())
	
if __name__ == "__main__":
	main()
