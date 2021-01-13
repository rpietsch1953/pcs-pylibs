# pcs-pylibs
PCS Python Libraries


NAME
    Param

DESCRIPTION
    Parameterverwaltung
            bedient die meisten Laufzeitparameter

CLASSES
    builtins.dict(builtins.object)
        Param
    
    class Param(builtins.dict)
     |  Param(Def={}, Args=None, Chk=None, Desc='', AddPar='')
     |  
     |  Main class and at the same time the result-dictionary.
     |  Normally imported with
     |  
     |  from pcs_argpass.Param import Param
     |  
     |    
     |  Method resolution order:
     |      Param
     |      builtins.dict
     |      builtins.object
     |  
     |  Methods defined here:
     |  
     |  GetLongOpts(self)
     |      Return list of long options
     |      (only? for debugging declarations)
     |      
     |      Returns:
     |          list: List of long options
     |  
     |  GetParDict(self)
     |      Return dict with references options -> parameter-names
     |      (only? for debugging declarations)
     |      
     |      Returns:
     |          dict: {option: name, ...}
     |  
     |  GetRemainder(self)
     |      Return list of additionel arguments on command-line
     |      
     |      Returns:
     |          list: List of additional arguments within runtime-arguments
     |  
     |  GetShortOpts(self)
     |      Return list of short options
     |      (only? for debugging declarations)
     |      
     |      Returns:
     |          str: List of short options
     |  
     |  Prepare(self)
     |      Prepare the class to be able to be used
     |      
     |      Raises:
     |          self.DeclarationError: if there are errors within the declaration-dict
     |  
     |  Process(self)
     |      Process the runtime-arguments
     |      
     |      Raises:
     |          self.ParamError: if an error occures within a parameter
     |          RuntimeError: if an internal error occures
     |  
     |  SetAddPar(self, AddPar='')
     |      Description of additional parameters for usage-function.
     |      printed in first line after "OPTIONS"
     |      
     |      Args:
     |          AddPar (str, optional): The text or additional parameters. Defaults to "".
     |      
     |      Raises:
     |          TypeError: if AddPar is not a string
     | 
     |  SetAllParams(self, AllParams = True)
     |      Set the flag for "All Params"
     |      Args:
     |          AllParams (bool, optional): If True, all params are initialized,
     |              at least with None. If False params with no default and no setting on
     |              the commandline are not defined within the dictionary. Defaults to True. 
     |
     |  SetArgs(self, Args=None)
     |      Set the argument list to process
     |      if None: use sys.argv as the arguments
     |      
     |      Args:
     |          Args ([type], optional): Runtime Arguments. Defaults to None.
     |      
     |      Raises:
     |          TypeError: If Args is not a list
     |  
     |  SetChk(self, Chk=None)
     |      Set the check-function. Not implementet now
     |      
     |      Args:
     |          Chk ([type], optional): [description]. Defaults to None.
     |      
     |      Raises:
     |          TypeError: if function is not of the proper type
     |  
     |  SetDef(self, Def={})
     |      Set the definition for processing arguments
     |      
     |      Args:
     |          Def (dict, optional): A definition-dict. Defaults to {}.
     |      
     |      Raises:
     |          TypeError: on error within the definition
     |      
     |      Describes the definition for arg-parsing.
     |      Def-dict: a dictionary of dictionaries
     |              { 'Name1': {.. declaration ..}, 
     |              ...
     |              'Name2': {.. declaration ..}, }
     |              "NameN" is the index under which at runtime you get the values 
     |                      within the resulting dictionary.
     |              The individual definitions look like:
     |                      {'s': 'a',
     |                      'l': 'longval', 
     |                      'o': True, 
     |                      'v':"LuLu",
     |                      'm': 't',
     |                      'd': 'Description',
     |                      'L': 'Low', 
     |                      'U': 'Up', 
     |                      'r': False },
     |              where:
     |                      m : Mode ->     t=Text, 
     |                                      b=Bool, 
     |                                      p=Path, 
     |                                      f=Existing File, 
     |                                      d=Exist. Dir, 
     |                                      i=Integer, 
     |                                      F=Float, 
     |                                      C=Counter (start default as 0 and increment each time found)
     |                              The following are processed BEVOR all others:
     |                                      H=Show help and exit
     |                                      x=Import config-file as json (file must exist loke "f")
     |                                      can be given more than once!
     |                              The following are processed AFTER all others:
     |                                      X=Export config as json to stdout und exit
     |                      r : Required -> True or False, False is default
     |                      s : Short Option(s) -> string or list or tuple of strings
     |                      l : Long Option(s) -> string or list or tuple of strings
     |                      o : Ein Parameter notendig -> True oder False, False is default
     |                      v : Default value -> if not given: 
     |                                      "" for Text, 
     |                                      False for Bool, 
     |                                      None for Path, File and Dir,
     |                                      0 for Int und Counter, 
     |                                      0. for Float
     |                      L : Lower Limit, value >= L if present
     |                      U : Upper Limit, value <= U if present
     |                      d : Description for helptext
     |              The entries "m" and ("s" or "l") must be present, all others are optional.
     |  
     |  SetDesc(self, Desc='')
     |      Set the description of the program
     |      for usage-string
     |      
     |      Args:
     |          Desc (str, optional): A descriptive string for the Program.
     |          printed bevore the parameters. Defaults to "".
     |      
     |      Raises:
     |          TypeError: if Desc is not a string.
     |  
     |  Usage(self)
     |      Return the helptext
     |      
     |      Returns:
     |          str: The help-text
     |  
     |  __init__(self, Def={}, Args=None, Chk=None, Desc='', AddPar='')
     |      The construktor
     |      Args:
     |          Def (dict, optional): See SetDef(). Defaults to {}.
     |          Args ([type], optional): See SetArgs(). Defaults to None.
     |          Chk ([type], optional): See SetChk(). Defaults to None.
     |          Desc (str, optional): See SetDesc(). Defaults to "".
     |          AddPar (str, optional): See SetAddPar. Defaults to "".
     |  
     |  
     |  ----------------------------------------------------------------------
     |  Data and other attributes defined here:
     |  
     |  DeclarationError = <class 'Param.Param.DeclarationError'>
     |      Diese Exception wird ausgelöst wenn in der Deklaration
     |      ein Fehler vorliegt.
     |      Dies ist im Konstructor oder den "SetXXX" Funktionen
     |      sowie in der "Prepare" Funktion  möglich.
     |  
     |  ParamError = <class 'Param.Param.ParamError'>
     |      Diese Exception wird ausgelöst wenn in fehler in den
     |      Laufzeitargumenten vorliegt.
     |      Dies ist in der "Process" Funktion möglich.
     |  

FUNCTIONS
    main()

DATA
    TestDef_1 = {'ConfFile': {'d': 'Zuerst die Werte aus der Datei lesen, ...

FILE
    /home/rainer/Wrk/Python/PCS-Lib/pcs-pylibs/pcs-argpass/Param.py


