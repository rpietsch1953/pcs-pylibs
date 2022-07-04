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

    
`SetupLogging(*, AppName: str, Verbose: int = 0, NoDaemon: bool = True, StdErr: bool = False, LogPath: str = '', LogFileInterval: int = 86400, LogFileCount: int = 14, Quiet: bool = False, LogProcInfo: bool = False, LogProcInfoModLen: int = 15, LogProcInfoFuncLen: int = 15, LogLevelType: int = 2, LogMultiProc: bool = False, LogMultiProcLen: int = 15, LogMultiThread: bool = False, LogMultiThreadLen: int = 15, LogStackOnDebug: str = 'NONE', LogStackDepth: int = 5, LogDebugIp: str = '127.0.0.1', LogDebugPort: int = 0, LogDebugCacheSize: int = 100, NoReset: bool = False) ‑> LogP.PortLogServer`
:   Creates a defined Log-setting with rich options
    
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
    
        LogPath (str, optional): Log to a Log-file. Defaults to ''.
                                Log to the file which is given as the argument.
                                this file is rotated on a daily base and holded up to 14 files
    
        LogFileInterval (int, optional): Number of seconds a logfile lasts until it is rotated.
                                Defaults to 60*60*24 => one day.
    
        LogFileCount (int, optional): Number of log-file kept. Defaults to 14.
    
        Quiet (bool, optional): Output only errors. Defaults to False.
    
        LogProcInfo (bool, optional): Show process and thread. Defaults to False.
    
        LogLevelType (int, optional): Format of LevelInfo. 0=None, 1=Number, 2=Name, 3=Both. 
                                    Defaults to 2.
    
        LogMultiProc (bool, optional): Show process-names. Defaults to False.
    
        LogMultiThread (bool, optional): Show thread-names. Defaults to False.
    
        LogStackOnDebug (str, optional): Log-level below or equal a call-stack trace is included.
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
    
        LogStackDepth (int, optional): Maximum number of call-stack entries to display. Defaults to 5.
    
        LogDebugPort (int, optional): If 0 no debug-server is started. Else the value has to be 
                                    between 1024 and 65535. A log-server is started on 'LogDebugIp' 
                                    at port 'LogDebugPort'. 
                                    It is possible to connect to this port (e.g with telnet) to 
                                    receive ALL log-messages from this program. ALL means really
                                    all, no mather which loglevel is set. This output also 
                                    includes all possible information about process, thread, 
                                    module and function. The stacktrace ('LogStackOnDebug') is also
                                    honored. This output can be really heavy, but can help to debug
                                    already running programs without the need to restart with 
                                    another loglevel.
                                    This server runs as a separated process and you have to 
                                    terminate it by calling the'Stop' and afterward 'Join' or 
                                    'Kill'-function of the returned 'PortLogServer'-object, 
                                    otherwise this process may block the termination of your 
                                    program. This server will restart himselve if it is terminated 
                                    by any means except you call the above mentioned functions.
                                    This port has to be free. Defaults to 0.
                                    
        LogDebugIp (str, optional): The IP-address to bind to. This address must exist on the host 
                                    this program is running. '0.0.0.0' for 'all IPs' is also 
                                    valid. Only examined if 'LogDebugPort' > 0. 
                                    Defaults to '127.0.0.1',
                                    
        LogDebugCacheSize (int, optional): Only used if 'LogDebugPort' > 0. This is the number of 
                                    log-messages cached for use at a new connection to the 
                                    server. So if someone connects to the server he receives the
                                    last 'LogDebugCacheSize' log messages and after them all new 
                                    messages.
                                    This is like a history. if set to 0 this function is disabled.
                                    Defaults to 100.
    
        NoReset (bool, optional): Do not reset logger on init. Defaults to False.
                                    Use with care. Could tend to mess up the logging.
    Output format:
        General overview:
            2022-06-22 07:37:42,494 Appname:MainProcess:MainThread LogP:main:461 - 40=   ERROR - Message
                                    ^       ^           ^          ^               ^     ^       ^
                                    |       |           |          |               |     |       |
            Name of application ----+       |           |          |               |     |       |
                only if not StdErr          |           |          |               |     |       |
            Name of procvess ---------------+           |          |               |     |       |
                if LogMultiProc = true                  |          |               |     |       |
            Name of thread if --------------------------+          |               |     |       |
                LogMultiThread = true                              |               |     |       |
            Module, function and linenumber -----------------------+               |     |       |
                only if LogProcInfo = true                                         |     |       |
            Level-number of message if LogLevelType = 1 or 3 ----------------------+     |       |
            Level-name of message if LogLevelType = 2 or 3 ------------------------------+       |
            The message given to the log-call ---------------------------------------------------+
    
            The minimal log entry for StdErr is:
                2022-06-22 07:37:42,494 Errormessage
            The maximal log entry is shown above.
    
        The output format to StdErr is like this:
            2022-06-22 07:37:42,494 MainProcess:MainThread LogP:main:461     - 40=   ERROR - Message
                No "Appname" because you know whitch program is running 
    
        The output format to sylog like this:
            Appname:MainProcess:MainThread LogP:main:461 - 40=   ERROR - Errormessage
                No timestamp because syslogg adds his own timestamp.
    
        The output format to a logfile is like this:
            2022-06-22 07:37:42,494 Appname:MainProcess:MainThread LogP:main:461 - 40=   ERROR - Message
    
    
        if a call-stack trace is requested lines like these are appended:
                File "./LogP.py", line 471, in <module>
                main()
                File "./LogP.py", line 448, in main
                abc()
                File "./LogP.py", line 411, in abc
                LogP.debug('Debug')

Classes
-------

`DummyPortLogServer(*args, **kwargs)`
:   The dummy-version of the 'PortLogServer'-class
    This class is used to return it to a user if no real Log-server is requested.
    So the programmer can call the functions without the need to question if
    a real server is running. All functions are No-Ops.

    ### Instance variables

    `IsAlive: bool`
    :

    `Name: str`
    :

    `Port: int`
    :

    `RunFlag: bool`
    :

    ### Methods

    `Join(self, *args, **kwargs) ‑> NoneType`
    :

    `Kill(self) ‑> NoneType`
    :

    `PollRestart(self) ‑> NoneType`
    :

    `Run(self, *args, **kwargs) ‑> NoneType`
    :

    `Stop(self, *args, **kwargs) ‑> NoneType`
    :

`PortLogQueueHandler(ProcClass: LogP.PortLogServer, *args, **kwargs)`
:   A queue-handler that allowes the automatic restart of the Log-server
    
    Args:
        ProcClass (PortLogServer): An instance of the listening PortLogServer.
                                    Needet to automatically restart if the
                                    server is terminated. All other parametrs
                                    look at the documentation of 
                                    'logging.handlers.QueueHandler'

    ### Ancestors (in MRO)

    * logging.handlers.QueueHandler
    * logging.Handler
    * logging.Filterer

    ### Methods

    `enqueue(self, record)`
    :   Overwritten enqueue function of the 'logging.handlers.QueueHandler' class.

`PortLogServer(*, host: str = '127.0.0.1', port: int = 0, name: str = '', queue: <bound method BaseContext.Queue of <multiprocessing.context.DefaultContext object at 0x7f019bf1ea00>> = None, logsize: int = 0, format: str = '')`
:   Send the messages from the input-Queue to a tcp-client
    on the defined address and port.
    
    Args:
        port (int, optional): The port to use (1024 to 65535). Defaults to 0.
        name (str, optional): The process-name of this class. Defaults to ''.
        queue (multiprocessing.Queue, optional): The input queue. Defaults to None.
        logsize (int, optional): if >0 logsize messages are buffered and send to the client on connection. Defaults to 0.
    
    Raises:
        ValueError: if invalid arguments are given.

    ### Instance variables

    `IsAlive: bool`
    :   Returnm True if the process is alive

    `Name: str`
    :   Return the process-name of this instance

    `Port: int`
    :   Return the port-number of this instance

    `RunFlag: bool`
    :   Return True if the process is running

    ### Methods

    `Join(self, Timeout: float = None) ‑> NoneType`
    :   Join this process
        If the optional argument timeout is None (the default), the method blocks until 
        the process whose join() method is called terminates. If timeout is a positive 
        number, it blocks at most timeout seconds. Note that the method returns None 
        if its process terminates or if the method times out.

    `Kill(self) ‑> NoneType`
    :   Kill this process

    `PollRestart(self) ‑> NoneType`
    :   Restart the process if it is not alive

    `Run(self, *, name: str = '', queue: <bound method BaseContext.Queue of <multiprocessing.context.DefaultContext object at 0x7f019bf1ea00>> = None) ‑> NoneType`
    :   Starts the reader-process
        
        Args:
            name (str, optional): Can overwrite the process-name of this instance. Defaults to ''.
            queue (multiprocessing.Queue, optional): can overwrite the input queue of this instance. 
                        If not given the name from the creation is used Defaults to None.
        
        Raises:
            ValueError: if invalid arguments are given.

    `Stop(self) ‑> NoneType`
    :   Stop the reader-process
