Module LogP
===========
Set up a logging-environment for daemons or console-programs

Variables
---------

    
`debug`
:   Debug logging function
    usage: LogP.debug("Msg")

    
`error`
:   Error logging function
    usage: LogP.error("Msg")

    
`info`
:   Info logging function
    usage: LogP.info("Msg")

    
`log`
:   Log logging function
    usage: LogP.log(level,"Msg")

    
`msg`
:   Msg logging function
    usage: LogP.msg("Msg")

    
`status`
:   Status logging function
    usage: LogP.status("Msg")

    
`trace`
:   Trace logging function
    usage: LogP.trace("Msg")

    
`warning`
:   Warning logging function
    usage: LogP.warning("Msg")

Functions
---------

    
`SetupLogging(AppName: str, Verbose: int = 0, NoDaemon: bool = True, StdErr: bool = False, LogFile: str = '', LogFileInterval: int = 86400, LogFileCount: int = 14, Quiet: bool = False, ProcInfo: bool = False, LevelInfo: bool = True, LevelType: int = 2, MultiProc: bool = False, MultiThread: bool = False, StackOnDebug: str = 'NONE', StackDepth: int = 5, NoReset: bool = False)`
:   Erzeugt eine definierte Log-Umgebung
    
    Args:
        AppName (str): Name of application
    
        Verbose (int, optional): Detail of logging. Defaults to 0.
                                0 = ERROR and STATUS
                                1 = MSG, WARNING, STATUS, ERROR 
                                2 = INFO, MSG, WARNING, STATUS, ERROR 
                                3 = DEBUG, INFO, MSG, WARNING, STATUS, ERROR 
                                4 = TRACE, DEBUG, INFO, MSG, WARNING, STATUS, ERROR 
    
        NoDaemon (bool, optional): Is this an terminal-task. Defaults to True.
                                If this is false => i am a daemon.
                                On deamons output to StdErr do not make sense, so this is ignored
                                and "syslog" or "logfile" is used.
    
        StdErr (bool, optional): Log to StdErr. Defaults to False.
                                If this is set the log goes to StdErr.
                                Ignored if we are a daemon.
    
        LogFile (str, optional): Log to a Log-file. Defaults to ''.
                                Log to the file which is given as the argument.
                                this file is rotated on a daily base and holded up to 14 files
    
        LogFileInterval (int, optional): Number of seconds a logfile lasts until it is rotated.
                                Defaults to 60*60*24 => one day.
    
        LogFileCount (int, optional): Number of log-file kept. Defaults to 14.
    
        Quiet (bool, optional): Output only errors. Defaults to False.
    
        ProcInfo (bool, optional): Show process and thread. Defaults to False.
    
        LevelType (int, optional): Format of LevelInfo. 0=None, 1=Number, 2=Name, 3=Both. Defaults to 2.
    
        MultiProc (bool, optional): Show process-names. Defaults to False.
    
        MultiThread (bool, optional): Show thread-names. Defaults to False.
    
        StackOnDebug (str, optional): Log-level below or equal a call-stack trace is included.
                                    Defaults to "NONE" => Disabled.
                                    The levels are:
                                        "ERROR"
                                        "STATUS"
                                        "WARNING"
                                        "MSG"
                                        "INFO"
                                        "DEBUG"
                                        "TRACE"
                                        "NONE"
                                    All other values are interpretet as "NONE".
                                    Value is not case-sensitive.
    
        StackDepth (int, optional): Maximum number of call-stack entries to display. Defaults to 5.
    
        NoReset (bool, optional): Do not reset logger on init. Defaults to False.
                                Use with care. Could tend to mess up the logging.
    Output format:
        General overview:
            2022-06-22 07:37:42,494 Appname:MainProcess:MainThread LogP:main:461 - 40=   ERROR - Errormessage
                                    ^       ^           ^          ^               ^     ^       ^
                                    |       |           |          |               |     |       |
            Name of application ----+       |           |          |               |     |       |
                only if not StdErr          |           |          |               |     |       |
            Name of procvess ---------------+           |          |               |     |       |
                if MultiProc = true                     |          |               |     |       |
            Name of thread if --------------------------+          |               |     |       |
                MultiThread = true                                 |               |     |       |
            Module, function and linenumber -----------------------+               |     |       |
                only if ProcInfo = true                                            |     |       |
            Level-number of message if LevelType = 1 or 3 -------------------------+     |       |
            Level-name of message if LevelType = 2 or 3 ---------------------------------+       |
            The message given to the log-call ---------------------------------------------------+
    
            The minimal log entry for StdErr is:
                2022-06-22 07:37:42,494 Errormessage
            The maximal log entry is shown above.
    
        The output format to StdErr is like this:
            2022-06-22 07:37:42,494 MainProcess:MainThread LogP:main:461     - 40=   ERROR - Errormessage
                No "Appname" because you know whitch program is running 
    
        The output format to sylog like this:
            Appname:MainProcess:MainThread LogP:main:461 - 40=   ERROR - Errormessage
                No timestamp because syslogg adds his own timestamp.
    
        The output format to a logfile is like this:
            2022-06-22 07:37:42,494 Appname:MainProcess:MainThread LogP:main:461 - 40=   ERROR - Errormessage
    
    
        if a call-stack trace is requested lines like these are appended:
              File "./LogP.py", line 471, in <module>
                main()
              File "./LogP.py", line 448, in main
                abc()
              File "./LogP.py", line 411, in abc
                LogP.debug('Debug')
