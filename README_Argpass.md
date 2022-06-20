Module Param
============
Parameterverwaltung
        bedient die meisten Laufzeitparameter

Functions
---------

    
`Trans(*, Type: str, Param: str, Path: str, FullPath: str, Msg: str, OptList: str) ‑> str`
:   

    
`main()`
:   

Classes
-------

`Param(Def: dict = {}, Args: list = None, Chk=None, Desc: str = '', AddPar: str = '', AllParams: bool = True, UserPars: dict = None, UserModes: dict = None, Translate=None)`
:   Main class and also the result-dictionary
    normally imported as
    
    from pcs_argpass.Param import Param
            
    
    The construktor
    Args:
        Def (dict, optional): See SetDef(). Defaults to {}.
        Args ([type], optional): See SetArgs(). Defaults to None.
        Chk ([type], optional): See SetChk(). Defaults to None.
        Desc (str, optional): See SetDesc(). Defaults to "".
        AddPar (str, optional): See SetAddPar. Defaults to "".
        AllParams (Boolean, optional): See SetAllParams. Defaults to True.
        UserPars (dict, optional): See SetUserKeys. Defaults to None.
        UserModes (dict, optional): See SetUserKeys. Defaults to None.

    ### Ancestors (in MRO)

    * builtins.dict

    ### Class variables

    `DeclarationError`
    :   s exception is raised if there is an declaration error within the 
        parameters of the class.

    `ParamError`
    :   s exception is raised if there is an error within the runtime-parameters.
        s os only within the "Process"-function.

    ### Methods

    `GetLongOpts(self) ‑> list`
    :   Return list of long options
        (only? for debugging declarations)
        
        Returns:
            list: List of long options

    `GetParDict(self) ‑> dict`
    :   Return dict with references options -> parameter-names
        (only? for debugging declarations)
        
        Returns:
            dict: {option: name, ...}

    `GetRemainder(self) ‑> list`
    :   Return list of additionel arguments on command-line
        
        Returns:
            list: List of additional arguments within runtime-arguments

    `GetShortOpts(self) ‑> list`
    :   Return list of short options
        (only? for debugging declarations)
        
        Returns:
            str: List of short options

    `MyProgName(self) ‑> str`
    :   Return the program-name
        
        Returns:
            str: Name of the executeable

    `MyProgPath(self) ‑> str`
    :   Return the program-path
        
        Returns:
            str: Path of the executeable

    `MyPwd(self) ‑> str`
    :   Return the directory at invocation of "Process"
        
        Returns:
            str: Directory at "Process"-time

    `Process(self) ‑> NoneType`
    :   Process the runtime-arguments
        
        Raises:
            self.ParamError: if an error occures within a parameter
            RuntimeError: if an internal error occures

    `SetAddPar(self, AddPar: str = '') ‑> NoneType`
    :   Description of additional parameters for usage-function.
        printed in first line after "OPTIONS"
        
        Args:
            AddPar (str, optional): The text or additional parameters. Defaults to "".
        
        Raises:
            TypeError: if AddPar is not a string

    `SetAllParams(self, AllParams: bool = True) ‑> NoneType`
    :   Set the flag for All Params
        
        Args:
            AllParams (bool, optional): If True, all params are initialized,
            at least with None. If False params with no default and no setting on
            the commandline are not defined within the dictionary. Defaults to True.

    `SetArgs(self, Args: list = None) ‑> NoneType`
    :   Set the argument list to process
        if None: use sys.argv as the arguments
        
        Args:
            Args ([type], optional): Runtime Arguments. Defaults to None.
        
        Raises:
            TypeError: If Args is not a list

    `SetChk(self, Chk=None)`
    :   Set the check-function. Not implementet now
        
        Args:
            Chk ([type], optional): [description]. Defaults to None.
        
        Raises:
            TypeError: if function is not of the proper type

    `SetDef(self, Def: dict = {}) ‑> NoneType`
    :   Set the definition for processing arguments
        
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
                        m : Mode ->     t=Text, 
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

    `SetDesc(self, Desc: str = '') ‑> NoneType`
    :   Set the description of the program
        for usage-string
        
        Args:
            Desc (str, optional): A descriptive string for the Program.
            printed bevore the parameters. Defaults to "".
        
        Raises:
            TypeError: if Desc is not a string.

    `SetTranslate(self, Translate=None) ‑> NoneType`
    :   Set translation routine for error-messages
        
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

    `SetUserKeys(self, UserPars: dict = None, UserModes: dict = None) ‑> NoneType`
    :   Set the key-table for the definition-dictionary
        
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

    `Usage(self) ‑> str`
    :   Return the helptext
        
        Returns:
            str: The help-text
