Module LogP
===========
Set up a logging-environment for daemons or console-programs
Usage:

    import logging
    from pcs_log.LogP import LogP

    .... you have to import this both in all your modules you like to
    use this logging. But you only need to SetupLogging once.

    .... Later within your program call this function:
    (You can call it more than once to change to another format)

LogP.SetupLogging(  AppName, Verbose, NoDaemon, StdErr, LogPath,
                    LogFileInterval, LogFileCount, Quiet,
                    LogProcInfo, LogProcInfoModLen,
                    LogProcInfoFuncLen, LogLevelType,
                    LogMultiProc, LogMultiProcLen,
                    LogMultiThread, LogMultiThreadLen,
                    LogStackOnDebug, LogStackDepth, LogDebugIp,
                    LogDebugPort, LogDebugCacheSize, NoReset,
                    LogLongLevel, translation)

--------------------------------------------------

    Args:
        All args are only named arguments!

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

        LogLongLevel (str, optional): Log-level below or equal a long info is included.
                                    Above this level except the ERROR-level the fields
                                        processname, threadname,module, line-no and levelinfo
                                    are not within the output.
                                    Alternative this can be a comma-separated list of levelnames
                                    in this case for this log-levels long infos are provided.
                                    Within this list "NONE" is ignored.
                                    Defaults to "DEBUG".
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

        LogStackDepth (int, optional): Maximum number of call-stack entries to display.
                                       Defaults to 5.

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

        transation (dict, optional): If given the programmer can overwrite the error-messages used.
                                    There are 2 functions to help creating this dict:
                                        LogP._PrintInitTranslation()
                                        LogP._PrintActualTranslation()
                                    they do exactly what their name says: they print either the
                                    default value for the translationtable or the actual value after
                                    overwriting some or all values with this dict.
                                    default = {}

--------------------------------------------------

After calling this function the new logging is set up. Use the standard functions
    logger.error, logger.warning, etc and additional you can use logger.msg,
    logger.status and logger.trace.
The severity is in descending order:
  ERROR, STATUS, WARNING, MSG, INFO, DEBUG, TRACE

--------------------------------------------------

 At the end of your program call:
    LogP.Stop()
this will stop the optional logger-process which send the output to a telnet-connection
if LogDebugPort is not 0.
--------------------------------------------------

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
