Module Param
============
Parameterverwaltung
    bedient die meisten Laufzeitparameter

Classes
-------

`Param(*, Def: dict = {}, Args: list = None, Chk=None, Desc: str = '', AddPar: str = '', AllParams: bool = True, UserPars: dict = None, UserModes: dict = None, ErrorOnUnknown: bool = True, HelpType: int = 0, Children: dict = {}, translation: dict = {})`
:   Main class and also the result-dictionary
        
    
    normally imported as
    
    from pcs_argpass.Param import Param, Translation_??_??
    
    This class can be used to create recursive sub-parameter classes.
    All children inherit the settings of their parents.
        Args:
            Def (dict, optional): See SetDef(). Defaults to {}.
            Args ([type], optional): See SetArgs(). Defaults to None.
            Chk ([type], optional): See SetChk(). Defaults to None.
            Desc (str, optional): See SetDesc(). Defaults to "".
            AddPar (str, optional): See SetAddPar. Defaults to "".
            AllParams (Boolean, optional): See SetAllParams. Defaults to True.
            UserPars (dict, optional): See SetUserKeys. Defaults to None.
            UserModes (dict, optional): See SetUserKeys. Defaults to None.
            HelpType (int, optional): Type of helptext.
                0: No Type, no standard defaults
                1: No Type, all defaults
                2: Type, no standard defaults
                3: Type and all defaults
            ErrorOnUnknown (bool, optional): If True an error is raised if
                there are undefined options on the commandline, If False: no error is raised.
                UnusedArgs is always populated with all undefined args from the commandline.
                This error is raised only on the topmost Param-object (not on children)
                Defaults to True.
                So if set to False you can test the 'UnusedArgs' property after return
                of the 'Process'-function to get the list of undefined args and process
                this situation on your own.
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
            translation: (dict, optional): A dictionary used for translating error messages.
                There are 2 'Hidden' function to help debug the translations:
                    _PrintInitTranslation() and
                    _PrintActualTranslation()
                This function do exactly what they say: print the values out to stdout. You can
                use them to get the exact values used. The following default may not be accurate
                at all - do not rely on this info, print the dict yourselve.
                 
                defaults to:
                    {
                    'PrefixError':
                        "Error in prefixed parameter {OptionName}",
                    'JsonError':
                        "Import failed '{wMsg}' in {OptionPath} ({FullPath}) for parameter {OptionName}",
                    'PathNoFile':
                        "The path '{OptionPath}' ({FullPath}) for parameter {OptionName} is not a file",
                    'PathNoDir':
                        "The path '{OptionPath}' ({FullPath}) for parameter {OptionName} is not a directory",
                    'PathNoPath':
                        "The path '{OptionPath}' ({FullPath}) for parameter {OptionName} is not valid on this filesystem",
                    'LessLow':
                        "Value '{OptValue}' for parameter {ParKey} is less than lower limit ({LowLimit})",
                    'HigherUp':
                        "Value '{OptValue}' for parameter {ParKey} is bigger than upper limit ({UppLimit})",
                    'NoInt':
                        "Value '{OptValue}' for parameter {ParKey} is not a valid integer",
                    'NoFloat':
                        "Value '{OptValue}' for parameter {ParKey} is not a valid floating point number",
                    'NoBool':
                        "Value '{OptValue}' for parameter {ParKey} is not valid boolean (YyTtJj1NnFf0)",
                    'OptionNotDefined':
                        "No action defined for {OptionName}",
                    'OptionRequired':
                        "{DefArgName} ({ParList}) required but not given",
                    'TypePath':
                        "path",
                    'TypeInteger':
                        "integer",
                    'TypeBool':
                        "bool",
                    'TypeFloat':
                        "float",
                    'TypeFile':
                        "file",
                    'TypeDir':
                        "directory",
                    'TypeCount':
                        "counter",
                    'TypeHelp':
                        "help",
                    'TypeImport':
                        "import",
                    'TypeExport':
                        "export",
                    'TypeGlobImport':
                        "global import",
                    'TypeGlobExport':
                        "global export",
                    'TypeStr':
                        "string",
                    'HelpDefault':
                        "Default",
                    'HelpValue':
                        "value",
                    'HelpUsage':
                        "Usage:",
                    'HelpOptions':
                        "Options:",
                    'HelpOptionInline':
                        "[OPTIONS ...]",
                    'OptionRequiresArgumentLong':
                        "option --{opt} requires argument",
                    'OptionNeedNoArgs':
                        "option --{opt} must not have an argument",
                    'OptionNotRecognizedLong':
                        "option --{opt} not recognized",
                    'ParNoUniquePrefix':
                        "option --{opt} not a unique prefix",
                    'OptionRequiresArgumentShort':
                        "option -{opt} requires argument",
                    'OptionNotRecognizedShort':
                        "option -{opt} not recognized",
                    'UndefinedOptionSingle':
                        "option {OptStr} not recognized",
                    'UndefinedOptionMultiple':
                        "options {OptStr} not recognized",
                    }
    
    NOTE:   All long options can be abbreviated to at least 2 characters or to the
            length making them unique within the defined long options.
            Example:
                you define 'automatic', 'autonom' and 'testopt'
                at the commandline this can be abbreviated to
                    PROG --autom --auton --te
                but not to
                    PROG --au
                because this is not unique within the optionlist.
    
    NOTE:   If children are used, the prefix-name is always optional, but if given, the option
            is ONLY recognized for this child. if there are the same long options for more
            then one child and NO prefix is given, this option is recognized by ALL children
            having this long option within their definition.
            Example:
                you define 'auto' within the root as 'MyOpt'
                you define 'auto' within the child 'alpha' as 'DoAuto'
    
                the commandline shald be
                    PROG --auto=yes
                then BOTH options are set to 'yes' e.g. MyParam['MyOpt'] == 'yes' AND MyParam['DoAuto'] == 'yes'
                with the commandline
                    PROG --alpha.auto=yes
                only MyParam['DoAuto'] == 'yes' and MyParam['MyOpt'] is either the default or not set depending on
                the definition of this option
                with the commandline
                    PROG --alpha.auto=yes --global.auto=no
                MyParam['MyOpt'] == 'no' AND MyParam['DoAuto'] == 'yes'
                REMEMBER: 'global' is ALWAYS the name of the root Param-object!
            please inform yout users about this possibility if you use child-definitions!

    ### Class variables

    `DeclarationError`
    :   this exception is raised if there is an declaration error within the
        parameters of the class.
        NOTE:   This error messages are NEVER translated since they are not user
                initiated errors.

    `GetoptError`
    :   Eigene Fehlerklasse für OptionError

    `ParamError`
    :   This exception is raised if there is an error within the runtime-parameters.
        This is only raised within the "Process"-function.
        NOTE:   This errors are translated with the 'translation' dictionary. There
                is the initial state of this dict using 'en_US' texts.
                This module also provide a 'Translation_de_DE' entry giving a german
                translation of the error-messages.
                If you can provide translations to other languages send me this
                declarations to <r.pietsch@pcs-at.com> and I will add them to this
                module.

    ### Instance variables

    `Child: dict`
    :   return all the children of this instance
        
        Returns:
            dict[str, Param]: Dictionary of the children of this instance

    `Definition: dict`
    :   returns s copy of the definition
        
        Returns:
            dict: a definition dictionary

    `FreeShortCommandLineParameter: str`
    :   Helper for programmers. can be used before "Process".
        Shound not be used in production environment
        
        Returns:
            str: A formatted, sorted list of all unused (free to use) short options
                broken to 68 characters a line.

    `FullPrefix: str`
    :   Returns the full qualified prefix of this instance
        e.g.: global.alpha.gamma
        if alpha is a child of global and gamma (this instance) is a child of alpha

    `GetExportDict`
    :   Return the dictionary for exporting all parameters
        
        Returns:
            dict: The complete parameter dictionary

    `LongOptsList: list`
    :   Return copied list of long options
        
        Returns:
            list: List of long options

    `OverviewCommandLineParameter`
    :   Helper for programmers. can be used before "Process".
        Shound not be used in production environment
        
        Returns:
            str: A formatted string giving all information about
                command-line parameters, broken to 68 characters a line.

    `ParDict: dict`
    :   Return copied dict with references options -> parameter-names
        
        Returns:
            dict: {option: name, ...}

    `Parents: str`
    :   Returns the full qualified parents of this instance
        e.g.: global.alpha
        if alpha is a child of global and gamma (this instance) is a child of alpha

    `PartPrefix: str`
    :   Returns the full qualified prefix without global of this instance
        e.g.: alpha.gamma
        if alpha is a child of global and gamma (this instance) is a child of alpha

    `Prefix: str`
    :   Return the prefix of this class
        
        Returns:
            str: the prefix value

    `ShortOptsList: list`
    :   Return copied list of short options

    `TestCommandLineParameter: str`
    :   Helper for programmers. can be used before "Process".
        Helps to find problems with the command-line interface.
        Prevent missunderstandig the interface by the user.
        Shound not be used in production environment
        
        Returns:
            str: A formatted sting giving all informations about errors
                or possible problems within the definition(s).

    `UnusedArgs: list`
    :   Return list of not defined args from the commandline
        This list is for the current Param-object and all of the children
        of this Param-object.
        So under normal conditions it makes only sense on the root of
        all Param-objects.
        
        Example:
            root defines '-z'
            child defines '-a'
            commandline is "-a -z --test"
        
            UnusedArgs of child is ['-z','--test']
            UnusedArgs of root = ['--test']     which is the correct list of undefined args.
        
        Returns:
            list: list of undefined args (str)

    `UsedLongCommandLineParameter: str`
    :   Helper for programmers. can be used before "Process".
        Shound not be used in production environment
        
        Returns:
            str: A formatted, sorted list of all used long options
                broken to 68 characters a line.

    `UsedShortCommandLineParameter: str`
    :   Helper for programmers. can be used before "Process".
        Shound not be used in production environment
        
        Returns:
            str: A formatted, sorted list of all used short options
                broken to 68 characters a line.

    ### Methods

    `AddChild(self, Prefix: str, Def: dict = {}, Description: str = '', Children: dict = {}, AddPar: str = '') ‑> NoneType`
    :   Add a child to a instance
        
        Args:
            Prefix (str): The unique name of this child. Will be translated to lower case.
                    can not be 'global' (this is the name of the topmost parent)
            Def (dict, optional): Definition for this instance (look at the constructor). Defaults to {}.
            Description (str, optional): Description of this instance. Defaults to ''.
            Children (dict, optional): Dictionary of children to the new instance (look at constructor). Defaults to {}.
            AddPar (str, optional): Additional parameter string of this instance. Defaults to ''.
        
        Raises:
            self.DeclarationError: If a parameter is invalid

    `GetCmdPar(self, Entry: str, dotted: bool = False, parents: bool = False) ‑> str`
    :   Return the commandline-options for one entry
        
        Args:
            Entry (str): The entry we are looking for
            dotted (bool, optional): show prefix for long params.
            parents (bool, optional): show also options from parents. Set also "dotted" to True
        
        Returns:
            str: the command-line options for this entry. E.g. "-h, --help"

    `GetRemainder(self) ‑> list`
    :   Return list of additionel arguments on command-line
        
        Returns:
            list: List of additional arguments within runtime-arguments

    `IsInherited(self, key: str) ‑> bool`
    :   Check if key is from parent
        
        Args:
            key (str): Key to search for
        
        Returns:
            bool: True if key is inherited from parent

    `IsOwnKey(self, key: str) ‑> bool`
    :   Check if the key is from the own optionset
        
        Args:
            key (str): Key to search for
        
        Returns:
            bool: True if key is in the own optionset

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

    `ParamStr(self, indent: int = 4, header: bool = True, allvalues: bool = True, dotted: bool = False, cmdpar: bool = True, parentopts: bool = False, recursive: bool = True) ‑> str`
    :   Returns a string with formatted output of the
                processed parameters.
        
                Args:
                    indent (int, optional): Number of leading spaces for children. Defaults to 4.
                            this value is multiplied with the generation. So grandchildren have
                            two times this number of leading spaces and children only one time
                            this number of spaces.
        
                    header (bool, optional): If True a header with the name of the object are added. Defaults to True.
        
                    allvalues (bool, optional): Outputs all avallable options for this child,
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
        global                     -> NoDaemon (-d, --[global.]nodaemon)              : False
        global                     -> Quiet    (-q, --[global.]quiet)                 : False
        global                     -> StdErr   (-s, --[global.]console)               : False
        global                     -> Verbose  (-v, --[global.]verbose)               : 2
            ------------------------------------------------------------
            global.alpha
            ------------------------------------------------------------
            global.alpha           -> Count    (-c, --[alpha.]count, --[alpha.]Count) : 7
            global.alpha           -> NoDaemon (-d, --[global.]nodaemon)              : False
            global.alpha           -> Quiet    (-q, --[global.]quiet)                 : False
            global.alpha           -> StdErr   (-s, --[global.]console)               : False
            global.alpha           -> Text     (-t, --[alpha.]text, --[alpha.]Text)   : ''
            global.alpha           -> Verbose  (-v, --[alpha.]verbose)                : 2
                ------------------------------------------------------------
                global.alpha.gamma
                ------------------------------------------------------------
                global.alpha.gamma -> Count    (-c, --[alpha.]count, --[alpha.]Count) : 7
                global.alpha.gamma -> NoDaemon (-d, --[global.]nodaemon)              : False
                global.alpha.gamma -> Quiet    (-q, --[global.]quiet)                 : False
                global.alpha.gamma -> StdErr   (-s, --[global.]console)               : False
                global.alpha.gamma -> Text     (-t, --[alpha.]text, --[alpha.]Text)   : ''
                global.alpha.gamma -> Verbose  (-v, --[alpha.]verbose)                : 2
                global.alpha.gamma -> Xy       (-b, --[gamma.]bbbb)                   : False
            ------------------------------------------------------------
            global.beta
            ------------------------------------------------------------
            global.beta            -> NoDaemon (-d, --[global.]nodaemon)              : False
            global.beta            -> Quiet    (-q, --[global.]quiet)                 : False
            global.beta            -> StdErr   (-s, --[global.]console)               : False
            global.beta            -> Verbose  (-v, --[beta.]verbose)                 : 5
        
                The shortest format is like (recursive = True):
        
        global -> NoDaemon  : False
        global -> Quiet     : False
        global -> StdErr    : False
        global -> Verbose   : 2
        alpha  -> Count     : 7
        alpha  -> Text      : ''
        alpha  -> Verbose   : 2
        gamma  -> Xy        : False
        beta   -> Verbose   : 5
        
                The shortest format is like (recursive = False):
        
        global -> NoDaemon  : False
        global -> Quiet     : False
        global -> StdErr    : False
        global -> Verbose   : 2
        
        ########################################################################################

    `Process(self) ‑> bool`
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
                        'v': "LuLu",
                        'm': 't',
                        'd': 'Description',
                        'L': 'Low',
                        'U': 'Up',
                        'r': False },
                where:
                        m : Mode ->
                                't' = Text,
                                'b' = Bool,
                                'p' = Path,
                                'f' = Existing File,
                                'd' = Exist. Dir,
                                'i' = Integer,
                                'F' = Float,
                                'C' = Counter (start default as 0 and increment each time found)
                                        Special case: short option takes no argument,
                                        long option NEEDS argument
                                        short option increments the value,
                                        long option adds the argument to the value
                        The following are processed BEVOR all others:
                                'H' = Show help and exit
                                'x' = Import config-file as json (file must exist like "f")
                                          can be given more than once!
                                '<' = MultiImport config-file as json
                        The following are processed AFTER all others:
                                'X' = Export config as json to stdout und exit
                                '>' = MultiExport config as json to stdout und exit
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

    `SetTranslation(self, translation: dict, IsChild: bool = False) ‑> NoneType`
    :   Setzt eine neue Translationtable
        
        Args:
            translation (dict): Dictionary mit übersetzten Fehlermeldungen
            IsChild (bool, optional): True wenn wir eine untergeordnete Instanz sind. Defaults to False.

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

    `items(self) ‑> list`
    :   Return the items list including the items of all parents
        
        Returns:
            list: the items

    `keys(self) ‑> list`
    :   Return the keys list including the keys of all parentsof
        
        Returns:
            list: the keys list

    `values(self) ‑> list`
    :   Return the values list including the values of all parents
        
        Returns:
            list: the values
