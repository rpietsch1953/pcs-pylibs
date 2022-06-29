#!/usr/bin/env python3
# vim: expandtab:ts=4:sw=4:noai

'''
Parameterverwaltung
    bedient die meisten Laufzeitparameter
'''
from re import X
import sys

import types
import inspect
from pathlib import Path, PurePath
import json
import types
import copy
import os
from itertools import chain

# Use json5 if it is avallable else use json 
try:
    import json5
    JsonLoads = json5.loads
    JsonLoad = json5.load
except:
    JsonLoads = json.loads
    JsonLoad = json.load
GLOBAL_NAME = 'global'

class Param():
    '''
Main class and also the result-dictionary
normally imported as

from pcs_argpass.Param import Param

This class can be used to create recursive sub-parameter classes.
All children inherit the settings of their parents. 
    '''
    class __ExceptionTemplate(Exception):
        def __call__(self, *args):
                return self.__class__(*(self.args + args))

        def __str__(self):
                return ': '.join(self.args)

    class DeclarationError(__ExceptionTemplate):
        '''
this exception is raised if there is an declaration error within the 
parameters of the class.
        '''
        pass

    class ParamError(__ExceptionTemplate):
        '''
This exception is raised if there is an error within the runtime-parameters.
This is only raised within the "Process"-function.
        '''
        pass

    class PathEncoder(json.JSONEncoder):
        """Subclass to encode path for json
        """        
        def default(self, z):
            """The "real" encoder

            Args:
                z (any): the object to encode

            Returns:
                any: the encoded Path or the default result
            """            
            if isinstance(z, Path) or isinstance(z, PurePath):
                return (str(z))             # return the string representation of the Path
            else:
                return super().default(z)   # let the default library do the work

        
    def __init__(   self, 
            Def: dict = {}, 
            Args: list = None, 
            Chk = None, 
            Desc: str = "", 
            AddPar: str = "", 
            AllParams: bool = True, 
            UserPars:dict = None, 
            UserModes: dict = None,
            Translate: callable = None,
            Children:dict = {}):
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
            Translate (callable): Function to translate error messages
            Children: (dict): Dictionary of Child-definition for this class.
                { 'Name': {'Def': {}, 'Desc': str, 'AddPar': str, 'Children': {} }, .... }  
                Name = The name of this child. Must be unique.   
                        Is translated to lower case.  
                        Can not bee "global" (this is the name of the root-class)  
                Def = A definition dictionary like our own "Def" parameter,  
                Children (optional) = dict of type Children, describes the grand-childer,  
                        this can be done to any level.   
                Desc (optional) = A string that describes this class (like our own "Desc"-parameter.  
                AddPar (optional) = String used as additional info like our own "AddPar"-parameter.  
        """

#---------------------------------------------
# Class-local Data
#---------------------------------------------
        self.__WorkDict = {}        # This is the result dictionary used to make the class look like dicktionary
        self.__Children: dict[str, __class__] = {}        # Dictionary of our children (all are our one class! )
        self.__Parent = None        # Our parent if we are a child 
        
        self.__MyProgName = ""      # the programm-name from __Argumente[0] (only name)
        self.__MyProgPath = ""      # the path of the executeable from __Argumente[0]
        self.__MyPwd = ""           # Actual directory at invocation of "Process" 
        self.__Definition = {}      # the definition-dict
        self.__Description = ""     # Description of program for help
        self.__Argumente = []       # list of commandline arguments
        self.__ChkFunc = None       # external check-funktion (not implemented jet)
        self.__UsageText = ""       # Complete help-text
        self.__ShortList = ""       # String of short parameters (e.g. "vhl:m:")
        self.__LongList = []        # List of Long parameters (e.g. "help","len="...)
        self.__ParDict = {}         # dict of "argtext" -> "Parameter-name"
        self.__RemainArgs = []      # List of remaining arguments from commandline
        self.__AddPar = ""          # Additional parameter Text (for help)
        self.__UsageTextList = []   # List of single help entries (also lists)
        self.__IsPrepared = False   # Marker if "Prepare" is run after changes
    
        self.__HelpList = []        # List of all parameters with type 'H'
        self.__ImportList = []      # List of all parameters with type 'x'
        self.__ExportList = []      # List of all parameters with type 'X'
        self.__Glob_ImportList = [] # List of all parameters with type '<'
        self.__Glob_ExportList = [] # List of all parameters with type '>'
        self.__AllParams = True     # True if all parameters are initialized, if False
                                    # only parameters with defaults or on the commandline
                                    # are in the dictionary
        self.__DoTranslate = None   # Translation routine for error-messages'
        self.__Prefix = GLOBAL_NAME
        self.__Glob_ExportStr = ''
 
        self.__WorkPars = {
            'shortpar':     's',
            'longpar':      'l', 
            'needoption':   'o', 
            'default':      'v',
            'mode':         'm',
            'description':  'd',
            'lowlimit':     'L', 
            'uplimit':      'U', 
            'required':     'r',
            'multiple':     'M'
            }
    
    
        self.__WorkModes = {
            'text':         't', 
            'bool':         'b', 
            'path':         'p', 
            'file':         'f', 
            'dir':          'd', 
            'int':          'i', 
            'float':        'F', 
            'count':        'C',
            'help':         'H',
            'import':       'x',
            'export':       'X',
            'glob_import':  '<',
            'glob_export':  '>'
            }
    
        self.__ModeToList = {
            self.__WorkModes['help']: self.__HelpList,
            self.__WorkModes['import']: self.__ImportList,
            self.__WorkModes['export']: self.__ExportList,
            self.__WorkModes['glob_import']: self.__Glob_ImportList,
            self.__WorkModes['glob_export']: self.__Glob_ExportList,
            }
# set the parameters with the individual functions
        self.__UserPars = UserPars
        self.__UserModes = UserModes
        self.SetDesc(Desc)
        self.SetUserKeys(UserPars = UserPars,UserModes = UserModes)
        self.SetDef(Def)
        self.SetArgs(Args)
        self.SetChk(Chk)
        self.SetAllParams(AllParams)
        self.SetAddPar(AddPar)
        self.SetTranslate(Translate)
        if Children is None:            # fix issue if Children is None
            Children = {}
        for wPrefix, wDict in Children.items():
            
            # Prefix (=Name) must be a string and not empty
            if type(wPrefix) != str:
                raise self.DeclarationError(f"Name of child '{wPrefix} is not a string")
            wPrefix = wPrefix.strip()
            if wPrefix == '':
                raise self.DeclarationError(f"Name of child could not be blank")
            
            # the declaration of a child has to bee a dictionary
            if type(wDict) != dict:
                raise self.DeclarationError(f"Child definition for '{wPrefix} is not a dictionary")
            
            # the declaration of a child needs at least a 'Def' entry whitch is a dictionary
            if 'Def' not in wDict:
                raise self.DeclarationError(f"Child definition for '{wPrefix} does not include 'Def'")
            if type(wDict['Def']) != dict:
                raise self.DeclarationError(f"'Def' in child definition for '{wPrefix} is not a dictionary")
            
            # if 'Children' not given set it to an empty dictionary
            if 'Children' not in wDict:
                wDict['Children'] = {}
            if wDict ['Children'] is None:
                wDict['Children'] = {}
                
            # the declaration of "Children" has to bee a dictionary
            if type(wDict['Children']) != dict:
                raise self.DeclarationError(f"'Children' in child definition for '{wPrefix} is not a dictionary")
            
            # if 'Desc' not given set it to ''
            if 'Desc' not in wDict:
                wDict['Desc'] = ''
                
            # the declaration of "Desc" has to bee a string
            if type(wDict['Desc']) != str:
                raise self.DeclarationError(f"'Desc' in child definition for '{wPrefix} is not a string")
            
            # if 'AddPar' not given set it to ''
            if 'AddPar' not in wDict:
                wDict['AddPar'] = ''
            
            # the declaration of "AddPar" has to bee a string
            if type(wDict['AddPar']) != str:
                raise self.DeclarationError(f"'AddPar' in child definition for '{wPrefix} is not a string")
            
            # now add all the children (if necessary also recursive)
            self.AddChild(Prefix = wPrefix, 
                          Def = wDict['Def'],  
                          Children = wDict['Children'], 
                          Description = wDict['Desc'],
                          AddPar = wDict['AddPar'])
        
        # show that we need preparation
        self.__IsPrepared = False

#
#---------------------------------------------
# Make the class look like a dictionary
# but this dictionary also includes all keys 
# of all the parents
#---------------------------------------------

    def __len__(self):
        """The Python __len__ method returns a positive integer that 
        represents the length of the object on which it is called. 
        It implements the built-in len() function.
        """        
        OwnLen = len(self.__WorkDict)
        if self.__Parent is None:
            return OwnLen
        return len(self.items())

    def __contains__(self, item):
        """The Python __contains__() magic method implements the 
        membership operation, i.e., the in keyword. Semantically, 
        the method returns True if the argument object exists in 
        the sequence on which it is called, and False otherwise.
        """        
        if item in self.__WorkDict:
            return True
        if self.__Parent is None:
            return False
        return item in self.__Parent

    def __getitem__(self, item):
        """Python’s magic method __getitem__(self, key) to 
        evaluate the expression self[key].
        """        
        if item in self.__WorkDict:
            return self.__WorkDict[item]
        return self.__Parent.__getitem__(item)

    def __setitem__(self, key, value):
        """Python’s magic method __setitem__(self, key, value) 
        implements the assignment operation to self[key].
        """        
        self.__WorkDict[key] = value

    def __delitem__(self, key):
        """Python’s magic method __delitem__(self, key) 
        implements the deletion of self[key].
        """
        self.__WorkDict.__delitem__(key)
        
    def __missing__(self, key):
        """The __missing__(self, key) method defines the behavior 
        of a dictionary subclass if you access a non-existent key. 
        More specifically, Python’s __getitem__() dictionary method 
        internally calls the __missing__() method if the key doesn’t 
        exist. The return value of __missing__() is the value to be 
        returned when trying to access a non-existent key.
        """
        if self.__Parent is None:
            raise KeyError(key)
        return self.__Parent[key]

    def __get__(self, instance, owner):
        """Python’s __get__() magic method defines the dynamic return 
        value when accessing a specific instance and class attribute. 
        It is defined in the attribute’s class and not in the class 
        holding the attribute (= the owner class). More specifically, 
        when accessing the attribute through the owner class, Python 
        dynamically executes the attribute’s __get__() method to 
        obtain the attribute value.  
        """
        return self.__get__(instance, owner)

    def __iter__(self):
        """The Python __iter__ method returns an iterator object. 
        An iterator object is an object that implements the __next__() 
        dunder method that returns the next element of the iterable 
        object and raises a StopIteration error if the iteration is done. 
        """
        if self.__Parent is None:
            return self.v.__iter__()
        else:
            return chain(self.__Parent__iter__(), self.v.__iter__())

    def IsOwnKey(self,key: str) -> bool:
        """Check if the key is from the own optionset

        Args:
            key (str): Key to search for

        Returns:
            bool: True if key is in the own optionset
        """        
        return key in self.__WorkDict

    def IsInherited(self, key: str) -> bool:
        """Check if key is from parent

        Args:
            key (str): Key to search for

        Returns:
            bool: True if key is inherited from parent
        """        
        return (not self.IsOwnKey(key))

    def keys(self) -> list:
        """Return the keys list including the keys of all parentsof 

        Returns:
            list: the keys list
        """        
        if self.__Parent is None:
            KeyList = list(self.__WorkDict.keys())
        else:
            KeyList = list(set(self.__Parent.keys()) | set(self.__WorkDict.keys()))
        try:
            KeyList.sort()
        except:
            pass
        return KeyList

    def values(self) -> list:
        """Return the values list including the values of all parents

        Returns:
            list: the values
        """        
        if self.__Parent is None:
            return self.__WorkDict.values()
        return self.__Parent.values() + self.__WorkDict.values()

    def items(self) -> list:
        """Return the items list including the items of all parents

        Returns:
            list: the items
        """        
        if self.__Parent is None:
            Res = list(self.__WorkDict.items())
            if Res is None:
                Res = []
        else:
            try:
                p = dict(self.__Parent.items())
#                p = list(self.__Parent.items())
            except:
                p = {}
#                p = []
            r = {}
            for key,value in p.items():
                r[key] = value
            for key,value in self.__WorkDict.items():
                r[key] = value
            Res = []
            for key,value in r.items():
                Res.append( (key, value))
            # Res = list({ **p , **dict(self.__WorkDict.items())})
#            Res = p + list(self.__WorkDict.items())
        try:
            Res.sort()
        except:
            pass
        return Res
#---------------------------------------------
# END Make the class look like a dictionary
#---------------------------------------------
#

    @property
    def Child(self) -> dict:
        """return all the children of this instance

        Returns:
            dict[str, Param]: Dictionary of the children of this instance
        """
        return self.__Children

    def AddChild(self, Prefix: str, Def: dict = {}, Description: str = '', Children: dict = {}, AddPar: str = '') -> None:
        """Add a child to a instance

        Args:
            Prefix (str): The unique name of this child. Will be translated to lower case.
                    can not be 'global' (this is the name of the topmost parent)
            Def (dict, optional): Definition for this instance (look at the constructor). Defaults to {}.
            Description (str, optional): Description of this instance. Defaults to ''.
            Children (dict, optional): Dictionary of children to the new instance (look at constructor). Defaults to {}.
            AddPar (str, optional): Additional parameter string of this instance. Defaults to ''.

        Raises:
            self.DeclarationError: If a parameter is invalid
        """        
        if type(Prefix) != str:
            raise self.DeclarationError(f"Prefix is not a string")
        p = Prefix.lower().strip()
        if p in self.__Children:
            raise self.DeclarationError(f"Prefix '{p}' is already used")
        if p == GLOBAL_NAME:
            raise self.DeclarationError(f"Prefix '{p}' is {GLOBAL_NAME} -> invalid!")
        self.__Children[p] = self.__class__( Def = Def,
                                    Args = self.__Argumente,
                                    Translate = self.__DoTranslate,
                                    UserPars = self.__UserPars,
                                    Desc = Description,
                                    Children = Children,
                                    AddPar = AddPar,
                                    AllParams = self.__AllParams
                                    )
        self.__Children[p].__Parent = self
        self.__Children[p].__Prefix = p



    def SetTranslate(self, Translate = None) -> None:
        """ Set translation routine for error-messages

        Args:
            Translate (callable, optional): Defaults to None.
Example:  
⠀⠀⠀⠀⠀⠀⠀⠀TransFunc(*,Type:str,Param:str, Path:str, FullPath:str, Msg:str, OptList:str) -> str:  
⠀⠀⠀⠀This function is called with the folowing parameters:  
⠀⠀⠀⠀⠀⠀⠀⠀Type, Param, Path, FullPath, Msg, OptList  
⠀⠀⠀⠀all of them are strings. The return value is the error-msg, also  
⠀⠀⠀⠀a string.  
⠀⠀⠀⠀The default messages are:  
⠀⠀⠀⠀⠀⠀⠀⠀if Type is "ImpFail"  
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"Import failed, {Path} for parameter {Param} is not a valid file"  
⠀⠀⠀⠀⠀⠀⠀⠀if Type is "ErrMsg"  
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"Error '{Msg}' in {Path} ({FullPath}) for parameter {Param}"  
⠀⠀⠀⠀⠀⠀⠀⠀if Type is "NoFile"  
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"The path {Path} ({FullPath}) for parameter {Param} is not a file"  
⠀⠀⠀⠀⠀⠀⠀⠀if Type is "NoPath"  
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"The path {Path} ({FullPath}) for parameter {Param} does not exist"  
⠀⠀⠀⠀⠀⠀⠀⠀if Type is "NoAct"  
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"No action defined for {Param}"  
⠀⠀⠀⠀⠀⠀⠀⠀if Type is "Required"  
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"{Param} ({OptList}) required but not given"  
⠀⠀⠀⠀⠀⠀⠀⠀for all other Type values  
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"Undefined error Type='{Type}', Param='{Param}', Path='{Path}', FullPath='{FullPath}', Msg='{Msg}', OptList='{OptList}'"  
⠀⠀⠀⠀If this function is given it has to translate ALL messages.  
⠀⠀⠀⠀If an error occures, the default messages are used  
  
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
        self.__IsPrepared = False   # we need a Prepare-call after this


    def SetDef(self, Def: dict = {}) -> None:
        """
        Set the definition for processing arguments

        Args:
            Def (dict, optional): A definition-dict. Defaults to {}.

        Raises:
            TypeError: on error within the definition
        
Describes the definition for arg-parsing.  
Def-dict: a dictionary of dictionaries  
⠀⠀⠀⠀{ 'Name1': {.. declaration ..},   
⠀⠀⠀⠀...  
⠀⠀⠀⠀'Name2': {.. declaration ..}, }  
⠀⠀⠀⠀"NameN" is the index under which at runtime you get the values   
⠀⠀⠀⠀⠀⠀⠀⠀within the resulting dictionary.  
⠀⠀⠀⠀The individual definitions look like:  
⠀⠀⠀⠀⠀⠀⠀⠀{'s': 'a',  
⠀⠀⠀⠀⠀⠀⠀⠀'l': 'longval',   
⠀⠀⠀⠀⠀⠀⠀⠀'o': True,   
⠀⠀⠀⠀⠀⠀⠀⠀'v': "LuLu",  
⠀⠀⠀⠀⠀⠀⠀⠀'m': 't',  
⠀⠀⠀⠀⠀⠀⠀⠀'d': 'Description',  
⠀⠀⠀⠀⠀⠀⠀⠀'L': 'Low',   
⠀⠀⠀⠀⠀⠀⠀⠀'U': 'Up',   
⠀⠀⠀⠀⠀⠀⠀⠀'r': False },  
⠀⠀⠀⠀where:  
⠀⠀⠀⠀⠀⠀⠀⠀m : Mode ->  
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀'t' = Text,   
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀'b' = Bool,   
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀'p' = Path,   
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀'f' = Existing File,   
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀'d' = Exist. Dir,   
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀'i' = Integer,   
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀'F' = Float,   
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀'C' = Counter (start default as 0 and increment each time found)  
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀Special case: short option takes no argument,  
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀long option NEEDS argument  
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀short option increments the value,  
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀long option adds the argument to the value  
⠀⠀⠀⠀⠀⠀⠀⠀The following are processed BEVOR all others:  
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀'H' = Show help and exit  
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀'x' = Import config-file as json (file must exist like "f")  
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀can be given more than once!  
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀'<' = MultiImport config-file as json  
⠀⠀⠀⠀⠀⠀⠀⠀The following are processed AFTER all others:  
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀'X' = Export config as json to stdout und exit  
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀'>' = MultiExport config as json to stdout und exit  
⠀⠀⠀⠀⠀⠀⠀⠀r : Required -> True or False, False is default  
⠀⠀⠀⠀⠀⠀⠀⠀s : Short Option(s) -> string or list or tuple of strings  
⠀⠀⠀⠀⠀⠀⠀⠀l : Long Option(s) -> string or list or tuple of strings  
⠀⠀⠀⠀⠀⠀⠀⠀o : Ein Parameter notendig -> True oder False, False is default  
⠀⠀⠀⠀⠀⠀⠀⠀v : Default value -> if not given:   
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"" for Text,   
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀False for Bool,   
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀None for Path, File and Dir,  
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀0 for Int und Counter,   
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀0. for Float  
⠀⠀⠀⠀⠀⠀⠀⠀L : Lower Limit, value >= L if present  
⠀⠀⠀⠀⠀⠀⠀⠀U : Upper Limit, value <= U if present  
⠀⠀⠀⠀⠀⠀⠀⠀d : Description for helptext  
⠀⠀⠀⠀The entries "m" and ("s" or "l") must be present, all others are optional.  
        """
        if type(Def) == dict:
            self.__Definition = Def
        else:
            raise TypeError('Def is not a dict')
        self.__IsPrepared = False   # we need a Prepare-call after this 

    @property
    def Definition(self) -> dict:
        """returns s copy of the definition

        Returns:
            dict: a definition dictionary
        """        
        return copy.deepcopy(self.__Definition)

    def GetCmdPar(self, Entry: str, dotted: bool = False, parents: bool = False) -> str:
        """Return the commandline-options for one entry

        Args:
            Entry (str): The entry we are looking for
            dotted (bool, optional): show prefix for long params. 
            parents (bool, optional): show also options from parents. Set also "dotted" to True

        Returns:
            str: the command-line options for this entry. E.g. "-h, --help"
        """        
        Erg = ""
        if parents:
            dotted = True
        try:
            SingleDef = self.__Definition[Entry]
        except:
            if parents:
                if self.__Parent is None:
                    return ''
                return self.__Parent.GetCmdPar(Entry = Entry, dotted = dotted, parents = parents)
            return ''
        try:
            wText = SingleDef[self.__WorkPars['shortpar']]
            for w in wText:
                if Erg != '':
                    Erg += ', '
                Erg += "-" + w 
        except:
            pass
        if dotted:
            Lp = '[' + self.__Prefix +'.]'
        else:
            Lp = ''
        try:
            wText = SingleDef[self.__WorkPars['longpar']]
            if type(wText) == list or type(wText) == tuple:
                for w in wText:
                    if Erg != '':
                        Erg += ', '
                    Erg += "--" + Lp + w 
            elif type(wText) == str:
                if Erg != '':
                    Erg += ', '
                Erg += "--" + Lp + wText
        except: 
            pass
        if Erg == '':
            if parents:
                if self.__Parent is not None:
                    Erg = self.__Parent.GetCmdPar(Entry = Entry, dotted = dotted, parents = parents)
        return Erg

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
        for c in self.__Children.values():
            c.SetArgs(Args)


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
        self.__IsPrepared = False   # we need a Prepare-call after this
        for c in self.__Children.values():
            c.SetChk(Chk)

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
        self.__IsPrepared = False   # we need a Prepare-call after this

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
        self.__IsPrepared = False   # we need a Prepare-call after this

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
        if self.__Prefix is None:
            wPrefText = ''
        else:
            if self.__Prefix != GLOBAL_NAME:
                wPrefText = f'active prefix = "{self.__Prefix}." only for long (--) options\n\n'
            else:
                wPrefText = ''
        wDesc = self.__Description
        if wDesc != '':
            wDesc += '\n\n'
        Text = f"Usage:\n{self.__MyProgName} OPTIONS {self.__AddPar}\n\n{wDesc}{wPrefText}Options:\n"
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
            if self.__Prefix is not None:
                if self.__Prefix != '' and self.__Prefix != GLOBAL_NAME:
                    ll = ll + len(self.__Prefix) + 3
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
                if self.__Prefix is not None:
                    if self.__Prefix != '' and self.__Prefix != GLOBAL_NAME and l != " ":
                        l = '[' + self.__Prefix + '.]' + l
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
#           Text += "\n"
        self.__UsageText = Text

    def Usage(self) -> str:
        """
        Return the helptext

        Returns:
            str: The help-text
        """
        if not self.__IsPrepared:
            self.__Prepare()
        Ret = self.__UsageText
        for n,c in self.__Children.items():
            Ret += f"\n    Child {n}\n"
            e = c.Usage()
            lines = e.splitlines()
            for l in lines:
                Ret += '    ' + l + '\n'
        return Ret

    def __Prepare(self) -> None:
        """
        Prepare the class to be able to be used

        Raises:
            self.DeclarationError: if there are errors within the declaration-dict
        """

        # clear all values
        self.__WorkDict.clear()
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
            
            if self.__WorkPars['multiple'] in ParKeys:
                ParMulti = SingleDef[self.__WorkPars['multiple']]
            else:
                ParMulti = False
                
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
                ##Test
                SingleDef[self.__WorkPars['needoption']] = True
            elif ParMode == self.__WorkModes['help']:
                Ut_Type = 'help'
            elif ParMode == self.__WorkModes['import']:
                Ut_Type = 'import'
                SingleDef[self.__WorkPars['needoption']] = True
            elif ParMode == self.__WorkModes['export']:
                Ut_Type = 'export'
            elif ParMode == self.__WorkModes['glob_import']:
                Ut_Type = 'glob_import'
                SingleDef[self.__WorkPars['needoption']] = True
            elif ParMode == self.__WorkModes['glob_export']:
                Ut_Type = 'glob_export'
            else:
                Ut_Type = 'string'

            if self.__WorkPars['default'] in ParKeys:
                if  SingleDef[self.__WorkPars['mode']] != self.__WorkModes['help'] \
                    and SingleDef[self.__WorkPars['mode']] != self.__WorkModes['import'] \
                    and SingleDef[self.__WorkPars['mode']] != self.__WorkModes['export'] \
                    and SingleDef[self.__WorkPars['mode']] != self.__WorkModes['glob_import'] \
                    and SingleDef[self.__WorkPars['mode']] != self.__WorkModes['glob_export']:
                    self.__WorkDict[ParName] = SingleDef[self.__WorkPars['default']]
                if ParMode == self.__WorkModes['file']:
                    wText = SingleDef[self.__WorkPars['default']]
                    try:
                        if wText[0] != "/":
                            wText = self.__MyPwd + '/' + wText
                        wFile = Path(wText).absolute()
                        if wFile.is_file:
                            self.__WorkDict[ParName] = str(wFile)
                    except:
                        wText = ''
                        self.__WorkDict[ParName] = wText
                elif ParMode == self.__WorkPars['description']:
                    wText = SingleDef[self.__WorkPars['default']]
                    if wText[0] != "/":
                        wText = self.__MyPwd + '/' + wText
                    wFile = Path(wText).absolute()
                    if wFile.is_dir:
                        self.__WorkDict[ParName] = str(wFile)
                elif ParMode == self.__WorkModes['path']:
                    wText = SingleDef[self.__WorkPars['default']]
                    if len(wText) > 0:
                        if wText[0] != "/":
                            wText = self.__MyPwd + '/' + wText
                        wFile = Path(wText).absolute()
                        self.__WorkDict[ParName] = str(wFile)
                    else:
                        self.__WorkDict[ParName] = ''
                Ut_Default = SingleDef[self.__WorkPars['default']]
            else:
                if self.__AllParams:
                    if ParMode == self.__WorkModes['bool']:
                        self.__WorkDict[ParName] = False
                    elif ParMode == self.__WorkModes['text']:
                        if ParMulti:
                            self.__WorkDict[ParName] = []
                        else:
                            self.__WorkDict[ParName] = ""
                    elif ParMode == self.__WorkModes['int']:
                        if ParMulti:
                            self.__WorkDict[ParName] = []
                        else:
                            self.__WorkDict[ParName] = 0
                    elif ParMode == self.__WorkModes['float']:
                        if ParMulti:
                            self.__WorkDict[ParName] = []
                        else:
                            self.__WorkDict[ParName] = 0.
                    elif ParMode == self.__WorkModes['count']:
                        self.__WorkDict[ParName] = 0
                    else:
                        if ParMode not in "xXH>":
                            if ParMulti:
                                self.__WorkDict[ParName] = []
                            else:
                                self.__WorkDict[ParName] = None
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
                        for ListPar in self.__ModeToList:
                            if ParMode == ListPar:
                                self.__ModeToList[ListPar].append('--' + ws)

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
                    for ListPar in self.__ModeToList:
                        if ParMode == ListPar:
                            self.__ModeToList[ListPar].append('--' + wText)
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
                            for ListPar in self.__ModeToList:
                                if ParMode == ListPar:
                                    self.__ModeToList[ListPar].append('-' + c)

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
                        for ListPar in self.__ModeToList:
                            if ParMode == ListPar:
                                self.__ModeToList[ListPar].append('-' + c)
                        Ut_Short.append(c)
                        self.__ShortList += c
                        if NeedOpt:
                            ##Test
                            if SingleDef[self.__WorkPars['mode']] != self.__WorkModes['count']:
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
        if Type == "Prefix":
            return f"Error in prefixed parameter {Param}"
        return f"Undefined error Type='{Type}', Param='{Param}', Path='{Path}', FullPath='{FullPath}', Msg='{Msg}', OptList='{OptList}'"

    def __Make_OptName(self,oIn):
        o = oIn
        if '.' in o:
            wList = o[2:].split('.')
            if len(wList) != 2:
                raise self.ParamError(self.__MakeErrorMsg(Type="Prefix",Param=o)) from None
            if wList[0] == self.__Prefix:
                o = '--' + wList[1]
        return o

    def Process(self) -> bool:
        """
        Process the runtime-arguments

        Raises:
            self.ParamError: if an error occures within a parameter
            RuntimeError: if an internal error occures
        """
        # print(self.__Prefix)
        Erg = False
        for c in self.__Children.values():
            if c.Process():
                Erg = True
            
        if not self.__IsPrepared:
            self.__Prepare()
        PreList = []
        for wPar in self.__Argumente[1:]:
            if wPar[0:2] == '--' and '.' in wPar:
                xPre = wPar[2:].split('.')[0]
                if xPre not in PreList:
                    PreList.append(xPre)
        wLongList = []
        for nLong in self.__LongList:
            wLongList.append(nLong)
        if len(PreList) > 0:
            for nPre in PreList:
                for nLong in self.__LongList:
                    wLongList.append(nPre + '.' + nLong)
        try:
#            opts, args = getopt.getopt(self.__Argumente[1:],self.__ShortList,self.__LongList)
            opts, args = _gnu_getopt(self.__Argumente[1:], self.__ShortList, wLongList, True)
        except GetoptError as exc:
            wMsg = exc.msg
            raise self.ParamError(wMsg) from None
        self.__RemainArgs = args
        for o, a in opts:
            o = self.__Make_OptName(o)
            if o in self.__HelpList:
                if self.__Prefix is not None:
                    if self.__Prefix != '':
                        print(f"#{'-'*60}\n# {self.__Prefix}\n#{'-'*60}\n")
                print(self.Usage())
                if self.__Parent is None:
                    sys.exit(0)
                return True
        for o,a in opts:
            o = self.__Make_OptName(o)
            if o in self.__Glob_ImportList:
                try:
                    n = Path(a).resolve()
                except:
                    raise self.ParamError(self.__MakeErrorMsg(Type="ImpFail",Path=a,Param=o)) from None
                if n.exists():
                    if n.is_file():
                        try:
                            wGlobDict = JsonLoad(n.open())
                        except Exception as exc:
                            wMsg = str(exc)
                            raise self.ParamError(self.__MakeErrorMsg(Type="ErrMsg",Msg=wMsg,Path=a,FullPath=n,Param=o)) from None
                        try:
                            wDict = wGlobDict[self.__Prefix]
                        except:
                            wDict = {}
                        for k in self.keys():
                            try:
                                self.__WorkDict[k] = wDict[k]
                            except:
                                pass
                    else:
                        raise self.ParamError(self.__MakeErrorMsg(Type="NoFile",Path=a,FullPath=n,Param=o)) from None
                else:
                    raise self.ParamError(self.__MakeErrorMsg(Type="NoPath",Path=a,FullPath=n,Param=o)) from None

        for o, a in opts:
            o = self.__Make_OptName(o)
            if o in self.__ImportList:
                try:
                    n = Path(a).resolve()
                except:
                    raise self.ParamError(self.__MakeErrorMsg(Type="ImpFail",Path=a,Param=o)) from None
                if n.exists():
                    if n.is_file():
                        try:
                            wDict = JsonLoad(n.open())
                        except Exception as exc:
                            wMsg = str(exc)
                            raise self.ParamError(self.__MakeErrorMsg(Type="ErrMsg",Msg=wMsg,Path=a,FullPath=n,Param=o)) from None
                        for k in self.keys():
                            try:
                                self.__WorkDict[k] = wDict[k]
                            except:
                                pass
                    else:
                        raise self.ParamError(self.__MakeErrorMsg(Type="NoFile",Path=a,FullPath=n,Param=o)) from None
                else:
                    raise self.ParamError(self.__MakeErrorMsg(Type="NoPath",Path=a,FullPath=n,Param=o)) from None
        for o, a in opts:
            o = self.__Make_OptName(o)
            if o in self.__HelpList:
                continue
            if o in self.__ImportList:
                continue
            if o in self.__Glob_ImportList:
                continue
            if o in self.__ExportList:
                continue
            if o in self.__Glob_ExportList:
                continue
            try:
                ParName = self.__ParDict[o] 
            except:
                continue
                raise RuntimeError(f"Error, option {o} not found in ParDict")
            try:
                wPar = self.__Definition[ParName]
            except:
                raise RuntimeError(f"Internal error, option {ParName} not found in Definition")
            if self.__WorkPars['needoption'] in wPar.keys():
                if wPar[self.__WorkPars['needoption']]:
                    Res = self.__CheckOption(ParName,o,wPar,a)
                    if not Res is None:
                        raise self.ParamError(Res)
                    if wPar[self.__WorkPars['mode']] != self.__WorkModes['count']:
                        continue
            if wPar[self.__WorkPars['mode']] == self.__WorkModes['bool']:
                try:
                    bVal = wPar[self.__WorkPars['default']]
                except:
                    bVal = False
                self.__WorkDict[ParName] = not bVal
            elif wPar[self.__WorkPars['mode']] == self.__WorkModes['count']:
                if '--' not in o:
                    self.__WorkDict[ParName] += 1
            else:
                raise self.ParamError(self.__MakeErrorMsg(Type="NoAct",Param=ParName))

        for o, a in opts:
            o = self.__Make_OptName(o)
            if o in self.__Glob_ExportList:
                self.__Glob_ExportStr = json.dumps(self.GetExportDict, sort_keys=True, indent=4, cls=self.PathEncoder)
                self.__Glob_ExportStr += '\n'
                if self.__Parent is None:
                    print(self.__Glob_ExportStr)
                    sys.exit(0)
                return True
            if o in self.__ExportList:
                if self.__Prefix is not None:
                    if self.__Prefix != '':
                        print(f"//{'-'*60}\n// {self.__Prefix}\n//{'-'*60}\n")
                print(json.dumps(self, sort_keys=True, indent=4, cls=self.PathEncoder))
                if self.__Parent is None:
                    sys.exit(0)
                return True

        for i in self.__Definition.keys():
            v = self.__Definition[i]
            Req = False
            if self.__WorkPars['required'] in v.keys():
                Req = v[self.__WorkPars['required']]
            if Req:
                if not i in self.keys():
                    raise self.ParamError(self.__MakeErrorMsg(Type="Required",Param=i,OptList=self.__GetOptList(i))) from None
        return Erg

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
            None    if no error
            Error-msg   if option is erroneous
        """
        wMod = wPar[self.__WorkPars['mode']]
# Prüfen ob Multiple gesetzt ist        
        try:
            wMulti = wPar[self.__WorkPars['multiple']]
        except:
            wMulti = False
#-------------------------
# Text
#-------------------------
        if wMod == self.__WorkModes['text']:
            if wMulti:
                if ParName not in self:
                   self.__WorkDict[ParName] = [] 
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
            if wMulti:
                self.__WorkDict[ParName].append(a)
            else:
                self.__WorkDict[ParName] = a
            return None
#-------------------------
# Integer
#-------------------------
        if wMod == self.__WorkModes['int']:
            if wMulti:
                if ParName not in self:
                   self.__WorkDict[ParName] = [] 
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
            if wMulti:
                self.__WorkDict[ParName].append(n)
            else:
                self.__WorkDict[ParName] = n
            return None
#-------------------------
# Count
#-------------------------
        if wMod == self.__WorkModes['count']:
            if a == '':
                return None
            try:
                n = int(a)
            except:
                return f"Value {a} for parameter {ParKey} is not an integer"
            if ParName in self.__WorkDict:
                self.__WorkDict[ParName] += n
            else:
                self.__WorkDict[ParName] = n
            return None
#-------------------------
# Float
#-------------------------
        if wMod == self.__WorkModes['float']:
            if wMulti:
                if ParName not in self:
                   self.__WorkDict[ParName] = [] 
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
            if wMulti:
                self.__WorkDict[ParName].append(n)
            else:
                self.__WorkDict[ParName] = n
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
                self.__WorkDict[ParName] = True
                return None
            if n in 'n0':
                self.__WorkDict[ParName] = False
                return None
            return f"Value {a} for parameter {ParKey} is not valid"
#-------------------------
# File (existing)
#-------------------------
        if wMod == self.__WorkModes['file']:
            if wMulti:
                if ParName not in self:
                   self.__WorkDict[ParName] = [] 
            if a[0] != "/":
                a = self.__MyPwd + "/" + a
            try:
                n = Path(a).resolve()
            except:
                return f"The name {a} for parameter {ParKey} is not a valid path"
            if n.exists():
                if n.is_file():
                    if wMulti:
                        self.__WorkDict[ParName].append(n)
                    else:
                        self.__WorkDict[ParName] = n
                    return None
                else:
                    return f"The path {a} ({n}) for parameter {ParKey} is not a file"
            return f"The path {a} ({n}) for parameter {ParKey} does not exist"
#-------------------------
# Directory (existing)
#-------------------------
        if wMod == self.__WorkModes['dir']:
            if wMulti:
                if ParName not in self:
                   self.__WorkDict[ParName] = [] 
            if a[0] != "/":
                a = self.__MyPwd + "/" + a
            try:
                n = Path(a).resolve()
            except:
                return f"The name {a} for parameter {ParKey} is not a valid path"
            if n.exists():
                if n.is_dir():
                    if wMulti:
                        self.__WorkDict[ParName].append(n)
                    else:
                        self.__WorkDict[ParName] = n
                    return None
                else:
                    return f"The path {a} ({n}) for parameter {ParKey} is not a directory"
            return f"The path {a} ({n}) for parameter {ParKey} does not exist"
#-------------------------
# Path
#-------------------------
        if wMod == self.__WorkModes['path']:
            if wMulti:
                if ParName not in self:
                   self.__WorkDict[ParName] = [] 
            if a[0] != "/":
                a = self.__MyPwd + "/" + a
            try:
                n = Path(a).resolve()
            except:
                return f"The name {a} for parameter {ParKey} is not a valid path"
            if wMulti:
                self.__WorkDict[ParName].append(n)
            else:
                self.__WorkDict[ParName] = n
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

    @property
    def GetExportDict(self):
        """
        Return the dictionary for exporting all parameters 

        Returns:
            dict: The complete parameter dictionary
        """
        Erg = {}
        for k in self.__WorkDict.keys():
            Erg[k] = self.__WorkDict[k]
        cDict = {}
        for c in self.__Children.values():
            e = c.GetExportDict
            ek = list(e.keys())[0]
            ev = list(e.values())[0]
            cDict[ek] = ev
            
        Erg['Children'] = cDict
        return { self.__Prefix: Erg }

    @property
    def Prefix(self) -> str:
        """Return the prefix of this class
        
        Returns:
            str: the prefix value
        """        
        return self.__Prefix

    def ParamStr(self, 
                 indent: int = 4, 
                 header: bool = True, 
                 all: bool = True, 
                 dotted: bool = False, 
                 cmdpar: bool = True, 
                 parentopts: bool = False, 
                 recursive: bool = True) -> str:
        """Returns a string with formatted output of the
        processed parameters.

        Args:
            indent (int, optional): Number of leading spaces for children. Defaults to 4.
                    this value is multiplied with the generation. So grandchildren have
                    two times this number of leading spaces and children only one time
                    this number of spaces.

            header (bool, optional): If True a header with the name of the object are added. Defaults to True.
    
            all (bool, optional): Outputs all avallable options for this child, 
                    included the inherited options. Defaults to True.
                    
            dotted (bool, optional): If True the names of the parameters are prefixed with the names
                    of their parents. Defaults to False.
            
            cmdpar (bool, optional): If True the commandline-options ere included in the output. Defaults to True.
            
            parentopts (bool, optional): If True and cmdpar is also True the commandline-options of the parents 
                    are anso included in the output. Defaults to False.
                    
            recursive (bool, optional): If True all descendants are include in the output, 
                    else only the own parameters are included. Defaults to True.

        Returns:
            str: The formated string of the processed parameters
            
        
Examples:  
########################################################################################  
  
        Assuming:  
            the topmost level includes   
                "NoDaemon", "Quiet", "StdErr", and "Verbose"  
            child "alpha" includes  
                "Count", "Text" and "Verbose"  
            grandchild "alpha -> gamma" includes  
                "Xy"  
            child "beta" includes  
                "Verbose"  
                  
        The largest format is like:  
------------------------------------------------------------  
global  
------------------------------------------------------------  
global⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀->⠀NoDaemon⠀(-d,⠀--[global.]nodaemon)⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀:⠀False  
global⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀->⠀Quiet⠀⠀⠀⠀(-q,⠀--[global.]quiet)⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀:⠀False  
global⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀->⠀StdErr⠀⠀⠀(-s,⠀--[global.]console)⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀:⠀False  
global⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀->⠀Verbose⠀⠀(-v,⠀--[global.]verbose)⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀:⠀2  
⠀⠀⠀⠀------------------------------------------------------------  
⠀⠀⠀⠀global.alpha  
⠀⠀⠀⠀------------------------------------------------------------  
⠀⠀⠀⠀global.alpha⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀->⠀Count⠀⠀⠀⠀(-c,⠀--[alpha.]count,⠀--[alpha.]Count)⠀:⠀7  
⠀⠀⠀⠀global.alpha⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀->⠀NoDaemon⠀(-d,⠀--[global.]nodaemon)⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀:⠀False  
⠀⠀⠀⠀global.alpha⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀->⠀Quiet⠀⠀⠀⠀(-q,⠀--[global.]quiet)⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀:⠀False  
⠀⠀⠀⠀global.alpha⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀->⠀StdErr⠀⠀⠀(-s,⠀--[global.]console)⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀:⠀False  
⠀⠀⠀⠀global.alpha⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀->⠀Text⠀⠀⠀⠀⠀(-t,⠀--[alpha.]text,⠀--[alpha.]Text)⠀⠀⠀:⠀''  
⠀⠀⠀⠀global.alpha⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀->⠀Verbose⠀⠀(-v,⠀--[alpha.]verbose)⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀:⠀2  
⠀⠀⠀⠀⠀⠀⠀⠀------------------------------------------------------------  
⠀⠀⠀⠀⠀⠀⠀⠀global.alpha.gamma  
⠀⠀⠀⠀⠀⠀⠀⠀------------------------------------------------------------  
⠀⠀⠀⠀⠀⠀⠀⠀global.alpha.gamma⠀->⠀Count⠀⠀⠀⠀(-c,⠀--[alpha.]count,⠀--[alpha.]Count)⠀:⠀7  
⠀⠀⠀⠀⠀⠀⠀⠀global.alpha.gamma⠀->⠀NoDaemon⠀(-d,⠀--[global.]nodaemon)⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀:⠀False  
⠀⠀⠀⠀⠀⠀⠀⠀global.alpha.gamma⠀->⠀Quiet⠀⠀⠀⠀(-q,⠀--[global.]quiet)⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀:⠀False  
⠀⠀⠀⠀⠀⠀⠀⠀global.alpha.gamma⠀->⠀StdErr⠀⠀⠀(-s,⠀--[global.]console)⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀:⠀False  
⠀⠀⠀⠀⠀⠀⠀⠀global.alpha.gamma⠀->⠀Text⠀⠀⠀⠀⠀(-t,⠀--[alpha.]text,⠀--[alpha.]Text)⠀⠀⠀:⠀''  
⠀⠀⠀⠀⠀⠀⠀⠀global.alpha.gamma⠀->⠀Verbose⠀⠀(-v,⠀--[alpha.]verbose)⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀:⠀2  
⠀⠀⠀⠀⠀⠀⠀⠀global.alpha.gamma⠀->⠀Xy⠀⠀⠀⠀⠀⠀⠀(-b,⠀--[gamma.]bbbb)⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀:⠀False  
⠀⠀⠀⠀------------------------------------------------------------  
⠀⠀⠀⠀global.beta  
⠀⠀⠀⠀------------------------------------------------------------  
⠀⠀⠀⠀global.beta⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀->⠀NoDaemon⠀(-d,⠀--[global.]nodaemon)⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀:⠀False  
⠀⠀⠀⠀global.beta⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀->⠀Quiet⠀⠀⠀⠀(-q,⠀--[global.]quiet)⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀:⠀False  
⠀⠀⠀⠀global.beta⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀->⠀StdErr⠀⠀⠀(-s,⠀--[global.]console)⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀:⠀False  
    global.beta            -> Verbose  (-v, --[beta.]verbose)                 : 5  
  
        The shortest format is like (recursive = True):  
  
global⠀->⠀NoDaemon⠀⠀:⠀False  
global⠀->⠀Quiet⠀⠀⠀⠀⠀:⠀False  
global⠀->⠀StdErr⠀⠀⠀⠀:⠀False  
global⠀->⠀Verbose⠀⠀⠀:⠀2  
alpha⠀⠀->⠀Count⠀⠀⠀⠀⠀:⠀7  
alpha⠀⠀->⠀Text⠀⠀⠀⠀⠀⠀:⠀''  
alpha⠀⠀->⠀Verbose⠀⠀⠀:⠀2  
gamma⠀⠀->⠀Xy⠀⠀⠀⠀⠀⠀⠀⠀:⠀False  
beta⠀⠀⠀->⠀Verbose⠀⠀⠀:⠀5  
  
        The shortest format is like (recursive = False):  
  
global⠀->⠀NoDaemon⠀⠀:⠀False  
global⠀->⠀Quiet⠀⠀⠀⠀⠀:⠀False  
global⠀->⠀StdErr⠀⠀⠀⠀:⠀False  
global⠀->⠀Verbose⠀⠀⠀:⠀2  
  
########################################################################################

        """        
        return self.__ParamStr(depth = 0,
                               indent = indent,
                               header = header,
                               all = all,
                               dotted = dotted,
                               dottedbase = '',
                               cmdpar = cmdpar,
                               parentopts = parentopts,
                               recursive = recursive) 

    def __ParamStr(self, 
                 depth: int = 0, 
                 indent: int = 4, 
                 header: bool = True, 
                 all: bool = True, 
                 dotted: bool = False, 
                 dottedbase:str = '', 
                 cmdpar: bool = True, 
                 parentopts: bool = False, 
                 recursive: bool = True) -> str:
        """This is the internal procedure. Look at "ParamStr" for all the args
        depth and dottedbase are only used internaly so the user can't set them to the exported function

        Args:
            depth (int, optional): Depth of the aktual child. Defaults to 0.
            dottedbase (str, optional): basename of the actual child (e.g. all the names of the parents). Defaults to ''.

        Returns:
            str: The formated string of the processed parameters
        """        
        Erg = ''
        Ls = ' ' * (depth * indent)
        p = self.Prefix
        if dotted:
            if dottedbase != '':
                p = dottedbase + '.' + p
        if header:
            Erg += f"{Ls}{'-' * 60}\n{Ls}{p}\n{Ls}{'-' * 60}\n"
        TheItems = self.items()
        for key,value in TheItems:
            if all or self.IsOwnKey(key):
                if cmdpar:
                    OptStr = self.GetCmdPar(Entry = key, dotted = dotted, parents = parentopts)
                else:
                    OptStr = ''
                if OptStr != '':
                    OptStr = '(' + OptStr + ')'
                if type(value) == str:
                    Erg += f"{Ls}{p}\t-> {key}\t{OptStr}\t: '{value}'\n"
                else:
                    Erg += f"{Ls}{p}\t-> {key}\t{OptStr}\t: {value}\n"
        if recursive:
            for n in self.Child.values():
                Erg += n.__ParamStr(depth = depth + 1, 
                                  indent = indent, 
                                  header = header, 
                                  all = all, 
                                  dotted = dotted, 
                                  dottedbase = p, 
                                  cmdpar = cmdpar,
                                  parentopts = parentopts, 
                                  recursive = recursive)
        if depth == 0:           # Auf der höchsten Ebene
            l = [0,0,0]
            lList = []
            Lines = Erg.splitlines()
            for Line in Lines:
                if '\t' not in Line:
                    lList.append(Line)
                else:
                    w = Line.split('\t')
                    lList.append(w)             # gesplittete zeile anhängen
                    for i in range(3):
                        try:
                            ll = len(w[i])
                            if l[i] < ll:
                                l[i] = ll
                        except:
                            pass
            Erg = ''
            Pad = ' ' * (max(l) + 1)
            for Line in lList:
                if type(Line) == str:
                    Erg += Line + '\n'
                else:
                    wErg = ''
                    for i in range(3):
                        wErg += (Line[i] + Pad)[:l[i] + 1]
                    Erg += wErg + Line[3] + '\n'
        return Erg



class GetoptError(Exception):
    opt = ''
    msg = ''
    def __init__(self, msg, opt=''):
        self.msg = msg
        self.opt = opt
        Exception.__init__(self, msg, opt)

    def __str__(self):
        return self.msg

def _getopt(args, shortopts, longopts = [], AcceptAll = False):
    """getopt(args, options[, long_options]) -> opts, args

    Parses command line options and parameter list.  args is the
    argument list to be parsed, without the leading reference to the
    running program.  Typically, this means "sys.argv[1:]".  shortopts
    is the string of option letters that the script wants to
    recognize, with options that require an argument followed by a
    colon (i.e., the same format that Unix getopt() uses).  If
    specified, longopts is a list of strings with the names of the
    long options which should be supported.  The leading '--'
    characters should not be included in the option name.  Options
    which require an argument should be followed by an equal sign
    ('=').

    The return value consists of two elements: the first is a list of
    (option, value) pairs; the second is the list of program arguments
    left after the option list was stripped (this is a trailing slice
    of the first argument).  Each option-and-value pair returned has
    the option as its first element, prefixed with a hyphen (e.g.,
    '-x'), and the option argument as its second element, or an empty
    string if the option has no argument.  The options occur in the
    list in the same order in which they were found, thus allowing
    multiple occurrences.  Long and short options may be mixed.

    """

    opts = []
    if isinstance(longopts, str):
        longopts = [longopts]
    else:
        longopts = list(longopts)
    while args and args[0].startswith('-') and args[0] != '-':
        if args[0] == '--':
            args = args[1:]
            break
        if args[0].startswith('--'):
            opts, args = _do_longs(opts, args[0][2:], longopts, args[1:],AcceptAll)
        else:
            opts, args = _do_shorts(opts, args[0][1:], shortopts, args[1:],AcceptAll)

    return opts, args

def _gnu_getopt(args, shortopts, longopts = [], AcceptAll = False):
    """getopt(args, options[, long_options]) -> opts, args

    This function works like getopt(), except that GNU style scanning
    mode is used by default. This means that option and non-option
    arguments may be intermixed. The getopt() function stops
    processing options as soon as a non-option argument is
    encountered.

    If the first character of the option string is `+', or if the
    environment variable POSIXLY_CORRECT is set, then option
    processing stops as soon as a non-option argument is encountered.

    """

    opts = []
    prog_args = []
    if isinstance(longopts, str):
        longopts = [longopts]
    else:
        longopts = list(longopts)

    # Allow options after non-option arguments?
    if shortopts.startswith('+'):
        shortopts = shortopts[1:]
        all_options_first = True
    elif os.environ.get("POSIXLY_CORRECT"):
        all_options_first = True
    else:
        all_options_first = False

    while args:
        if args[0] == '--':
            prog_args += args[1:]
            break

        if args[0][:2] == '--':
            opts, args = _do_longs(opts, args[0][2:], longopts, args[1:], AcceptAll)
        elif args[0][:1] == '-' and args[0] != '-':
            opts, args = _do_shorts(opts, args[0][1:], shortopts, args[1:], AcceptAll)
        else:
            if all_options_first:
                prog_args += args
                break
            else:
                prog_args.append(args[0])
                args = args[1:]

    return opts, prog_args

def _do_longs(opts, opt, longopts, args, AcceptAll = False):
    try:
        i = opt.index('=')
    except ValueError:
        optarg = None
    else:
        opt, optarg = opt[:i], opt[i+1:]
    if AcceptAll:
        try:
            has_arg, opt = _long_has_args(opt, longopts)
        except GetoptError as exc:
            return opts, args
    else:
        has_arg, opt = _long_has_args(opt, longopts)
    if has_arg:
        if optarg is None:
            if not args:
                raise GetoptError('option --%s requires argument' % opt, opt)
            optarg, args = args[0], args[1:]
    elif optarg is not None:
        raise GetoptError('option --%s must not have an argument' % opt, opt)
    opts.append(('--' + opt, optarg or ''))
    return opts, args

# Return:
#   has_arg?
#   full option name
def _long_has_args(opt, longopts):
    possibilities = [o for o in longopts if o.startswith(opt)]
    if not possibilities:
        raise GetoptError('option --%s not recognized' % opt, opt)
    # Is there an exact match?
    if opt in possibilities:
        return False, opt
    elif opt + '=' in possibilities:
        return True, opt
    # No exact match, so better be unique.
    if len(possibilities) > 1:
        # XXX since possibilities contains all valid continuations, might be
        # nice to work them into the error msg
        raise GetoptError('option --%s not a unique prefix' % opt, opt)
    assert len(possibilities) == 1
    unique_match = possibilities[0]
    has_arg = unique_match.endswith('=')
    if has_arg:
        unique_match = unique_match[:-1]
    return has_arg, unique_match

def _do_shorts(opts, optstring, shortopts, args, AcceptAll = False):
    while optstring != '':
        opt, optstring = optstring[0], optstring[1:]
        if AcceptAll:
            try:
                wHasArgs = _short_has_arg(opt, shortopts)
            except GetoptError as exc:
                wHasArgs = False
        else:
            wHasArgs = _short_has_arg(opt, shortopts)
        if wHasArgs:
            if optstring == '':
                if not args:
                    raise GetoptError('option -%s requires argument' % opt, opt)
                optstring, args = args[0], args[1:]
            optarg, optstring = optstring, ''
        else:
            optarg = ''
        opts.append(('-' + opt, optarg))
    return opts, args

def _short_has_arg(opt, shortopts):
    for i in range(len(shortopts)):
        if opt == shortopts[i] != ':':
            return shortopts.startswith(':', i+1)
    raise GetoptError('option -%s not recognized' % opt, opt)
    
if __name__ == "__main__":

    GlobalDef = {
        'Help': {   
                's': 'h',
                'l': 'help',
                'm': 'H',
                'd': 'Diesen Hilfetext anzeigen und beenden'
                },
        'Export': { 
                's': 'x',
                'l': 'export',
                'm': 'X',
                'd': 'Ausgabe der aktuellen Konfiguration und Beenden'
                },
        'GlobalExport': { 
                'l': 'globexport',
                'm': '>',
                'd': 'Ausgabe aller Konfigurationen und Beenden'
                },
        'ConfFile': {   
                's': 'c',
                'l': 'config',
                'm': 'x',
                'd': '''Zuerst die Werte aus der Datei lesen, 
danach erst die Komandozeilenparameter'''
                },
            'Verbose': {
                's': 'v',
                'l': 'verbose',
                'r': False,
                'm': 'C',
                'd': """Ausgabe von Statusmeldungen
für mehr Details die kurze Option mehrmals angeben oder 
die lange Option mit einer höheren Zahl verwenden.""",
                },
            'Quiet': {
                's': 'q', 
                'l': 'quiet', 
                'm': 'b', 
                'd': 'Nur Fehler ausgeben'
                },
            'StdErr': {
                's': 's',
                'l': 'console',
                'm': 'b',
                'v': False,
                'd': """Ausgabe der Statusmeldungen auf die
Konsole und nicht auf syslog""",
                },
            'NoDaemon': {
                's': 'd',
                'l': 'nodaemon',
                'm': 'b',
                'v': False,
                'd': 'Start im Vordergrund (Nicht als Daemon) für Test',
                },
#             'LogPath': {   
#                 'l': 'logpath',
#                 'r': False,
#                 'M': True,
#                 'o': True,
#                 'm': 'p',
#                 'v': '',
#                 'd': 'Pfad zu einer Log-Datei. Diese wird täglich rotiert und neu erstellt'
#                 },
#             'LogProcInfo': {
#                 'l': 'logprocinfo',
#                 'm': 'b',
#                 'v': False,
#                 'd': 'Ausgabe der Procedur und der Zeile',
#                 },
#             'LogMultiProc': {
#                 'l': 'logmultiproc',
#                 'm': 'b',
#                 'v': False,
#                 'd': '''Nur wenn "logprocinfo" gesetzt ist.
# zusätzlich Ausgabe des Prozessnamens.
# Macht nur bei Programmen mit mehreren Prozessen sinn''',
#                 },
#             'LogMultiThread': {
#                 'l': 'logmultithread',
#                 'm': 'b',
#                 'v': False,
#                 'd': '''Nur wenn "logprocinfo" gesetzt ist.
# zusätzlich Ausgabe des Threadnamens.
# Macht nur bei Programmen mit mehreren Threads sinn''',
#                 },
#             'LogLevelType': {
#                 'l': 'logleveltype',
#                 'm': 'i',
#                 'v': 2,
#                 'd': '''Ausgabe des Loglevels.
# 0 = Keine Ausgabe
# 1 = Level-Nummer
# 2 = Level-Name
# 3 = Beide''',
#                 },
#             'LogStackOnDebug': {
#                 'l': 'logstack',
#                 'm': 't',
#                 'v': 'NONE',
#                 'd': '''Ausgabe des Anwendungsstacks ab diesem Level.
# Bei verwendung von "LogP" sind die Levels:
#     ERROR
#     STATUS
#     WARNING
#     MSG
#     INFO
#     DEBUG
#     TRACE
#     NONE
# Alle anderen Werte werden als "NONE" interpretiert
# Groß- oder Kleinschreibung wird ignoriert''',
#                 },
#             'LogStackDepth': {
#                 'l': 'logstackdepth',
#                 'm': 'i',
#                 'v': 0,
#                 'd': '''Anzahl der auszugebenden Stackzeilen, 0 = Disabled'''
#                 },
            
        }



    TestDef_Alpha =     {
        'Help': {   's': 'h',
                'l': 'help',
                'm': 'H',
                'd': 'Diesen Hilfetext anzeigen und beenden'},
    #     'Export': { 's': 'x',
    #             'l': 'export',
    #             'm': 'X',
    #             'd': 'Ausgabe der aktuellen Konfiguration und Beenden'},
    #     'ConfFile': {   's': 'z',
    #             'l': 'par',
    #             'm': 'x',
    #             'd': '''Zuerst die Werte aus der Datei lesen, 
    # danach erst die Komandozeilenparameter'''},
        'Verbose': {    's': 'v',
                'l': 'verbose',
                'r': False,
                'm': 'C',
                'd': 'Sei gesprächig'},
        'Count': {  's': 'c',
                'l': ('count','Count'),
                'r': True,
                'o': True,
                'v': 7,
                'm': 'i',
                'L': 1,
                'U': 10,
                'd': 'Eine Zahl zwischen 1 und 10'},
        'Text': {   's': 't',
                'l': ('text','Text'),
                'o': True,
                'v': '',
                'm': 't',
                'd': 'Ein Text'},
        # 'MultiText': {  's': 'T',
        #         'l': ('mtext','mText'),
        #         'o': True,
        #         'M': True,
        #         'm': 't',
        #         'd': 'Multi Text'},
        # 'Float': {  's': 'F',
        #         'l': ('float','Float'),
        #         'o': True,
        #         'v': 10.47,
        #         'm': 'F',
        #         'L': 1,
        #         'U': 100.2,
        #         'd': 'Eine Gleitkommazahl zwischen 1 und 100.2'},
        # 'File': {   's': 'f',
        #         'l': 'file',
        #         'o': True,
        #         'm': 'f',
        #         'd': 'Eine existierende Datei'},
        # 'Dir': {    's': 'D',
        #         'l': 'dir',
        #         'o': True,
        #         'm': 'd',
        #         'd': 'Ein existierendes Verzeichnis'},
        # 'Path': {   's': 'p',
        #         'l': 'path',
        #         'r': 'true',
        #         'M': True,
        #         'o': True,
        #         'm': 'p',
        #         'd': 'Ein gültiger Path'},
        # 'Counter': {    
        #         's': 'C',
        #         'o': False,
        #         'm': 'C',
        #         'd': 'Mehrmals zum hochzählen'},
        }
    TestDef_Beta =     {
        'Help': {   
                's': 'h',
                'l': 'help',
                'm': 'H',
                'd': 'Diesen Hilfetext anzeigen und beenden'
                },
        'Verbose': {
                's': 'v',
                'l': 'verbose',
                'r': False,
                'm': 'C',
                'd': 'Sei gesprächig'
                },
        }
    TestDef_Gamma =     {
        'Xy': {   
                's': 'b',
                'l': 'bbbb',
                'm': 'b',
                'd': 'Ein Switch'
                },
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

        m = Param(Def=GlobalDef, Children = { 
            'Alpha': 
                {
                'Desc': "Description Alpha", 
                'Def': TestDef_Alpha, 
                },
            'Beta':
                {
                'Def': TestDef_Beta, 
                'Desc': "Description Beta", 
                }
            }
            )
        m.Child['alpha'].AddChild(Prefix='Gamma', Def=TestDef_Gamma, Description="Eine eingefügte Ebene")
        try:
            m.SetArgs(Args = shlex.split('Test -vv --beta.verbose=3'))
 
            Erg = m.Process()
            # GlobPar = m.GlobalParam
        except Exception as exc:
            dir(exc)
            print(exc)
            return
        if Erg:
            return
        # m['TopLevel'] = 'Top'
        # m.Child['alpha']['AlphaLevel'] = 'Alpha'
        # m.Child['alpha'].Child['gamma']['GammaLevel'] = 'Gamma'
        
        print(f"{'*' * 60}All Options ON\n")
        print(m.ParamStr(dotted=True,parentopts=True))    
        
        print(f"{'*' * 60}Shortes\n")
        print(m.ParamStr(dotted=False,parentopts=False,indent=0,header=False,cmdpar=False,all=False))    
        
#         print(f"{'*' * 60}Dotted\n")
#         print(m.ParamStr(indent=0,dotted=True,cmdpar=True))    
        
#         print(f"{'*' * 60}Default\n")
#         print(m.ParamStr())    
        
#         print(f"{'*' * 60}No header\n")
#         print(m.ParamStr(indent=2, header=False))   
        
#         print(f"{'*' * 60}Not all\n")
#         print(m.ParamStr(indent=8,all=False,parentopts=True))    
        
#         print(f"{'*' * 60}Alpha Rec\n")
#         print(m.Child['alpha'].ParamStr(dotted = True, parentopts = True))    
        
#         print(f"{'*' * 60}No Rec\n")
#         print(m.ParamStr(recursive=False))    

#         print(f"{'*' * 60}\n")
#         print(f"{'-' * 60}\nGlobal\n{'-' * 60}")
#         for key,value in m.items():
#             print(f"Global -> {key}: {value}")
        
#         for Name, Par in m.Child.items():
#             print(f"{'-' * 60}\n{Name}\n{'-' * 60}")
#             for key,value in Par.items():
#                 print(f"{Name} -> {key}: {value}")
#         print(f"\n{'-' * 80}\n\n")        
#         print(m.Usage())
#         print(f"\n{'#' * 80}\n\n")



#         a = Param(Def = TestDef_Alpha, 
#             Desc = "Dies ist ein Test\ndas bedeutet hier steht nur\nnonsens", 
#             AddPar = "File .... File", 
#             Translate = Trans,
#             AllParams = True
#             )
#         # a.SetArgs(Args = shlex.split('Test -v -CCC -f /Mist --dir=/tmp'))
#         try:
#             a.Process()
#         except Exception as exc:
#             dir(exc)
#             print(exc)
#             return
#         for key,value in a.items():
#             print(key,value)
#         # print(dir(a))
#         print(f"ExportDict = {a.GetExportDict}")
#         print(f"Ergebnis: {a}")
#         print(f"Rest: {a.GetRemainder()}")
#         print(a.GetCmdPar('Text'))
#         print(a.Definition)
#         print(a.Usage())
#         print('-'*60)
#         b = Param(Def = TestDef_Beta, 
#             Desc = "Dies ist ein Test # 2", 
# #            AddPar = "File .... File", 
#             Translate = Trans,
#             AllParams = True
#             )
# #        b.SetArgs(Args = shlex.split('Test --ignore.help -v -x'))
#         try:
#             b.Process()
#         except Exception as exc:
#             dir(exc)
#             print(exc)
#             return
#         for key,value in b.items():
#             print(key,value)
#         # print(dir(a))
#         print(f"Ergebnis: {b}")
#         print(f"Rest: {b.GetRemainder()}")
#         print(b.GetCmdPar('Text'))
#         print(b.Definition)
#         print(b.Usage())
#         print('-'*60)
    main()
