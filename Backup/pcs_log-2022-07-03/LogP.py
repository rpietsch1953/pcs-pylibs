#!/usr/bin/env python3
# vim: expandtab:ts=4:sw=4:noai
"""
    Set up a logging-environment for daemons or console-programs
"""
import logging
import logging.config
import time
import os
import sys
import warnings
from PortLogServer import PortLogServer, PortLogQueueHandler, DummyPortLogServer
import multiprocessing
from functools import partial
#import LogP

_KEEP = 'keep'
_KEEP_WARN = 'keep-warn'
_RAISE = 'raise'
_OVERWRITE_WARN = 'overwrite-warn'

class _AddStackContextFilter(logging.Filter):
    def __init__(self, trim_amount: int = 5, below_level: int = -1):
        """Class to prepaire the "stack"-variable within logrecord

        Args:
            trim_amount (int, optional): Maximum number of stack-lines to show. Defaults to 5.
            below_level (int, optional): Log-leven below or equal a stacktrace is shown. Defaults to -1 => disabled.
        """        
        self.trim_amount = trim_amount
        self.below_level = below_level
        
    def IsLast(self,s):
        Such = '\n    root.log(level, msg, *args, **kwargs)\n'
        return Such in s        

    def filter(self, record):
        import traceback
        if record.levelno <= self.below_level:
            wStack = traceback.format_stack()
            ResStr = '\n'
            ResList = []
            for r in wStack:
                s = str(r)
                if self.IsLast(s):
                    break
                ResList.append(s)
            record.stack = '\n' + ''.join(ResList[0-self.trim_amount:])
        else:
            record.stack = ''
        return True

def _AddLoggingLevel(level_name, level_num, method_name=None,
                      if_exists=_KEEP, *, exc_info=False, stack_info=False):
    """
    
    This Part was copied from: Joseph R. Fox-Rabinovitz
    
    Comprehensively add a new logging level to the :py:mod:`logging`
    module and the currently configured logging class.

    The `if_exists` parameter determines the behavior if the level
    name is already an attribute of the :py:mod:`logging` module or if
    the method name is already present, unless the attributes are
    configured to the exact values requested. Partial registration is
    considered a conflict. Even a complete registration will be
    overwritten if ``if_exists in (OVERWRITE, OVERWRITE_WARN)`` (without
    a warning of course).

    This function also accepts alternate default values for the keyword
    arguments ``exc_info`` and ``stack_info`` that are optional for
    every logging method. Setting alternate defaults allows levels for
    which exceptions or stacks are always logged.

    Parameters
    ----------
    level_name : str
        Becomes an attribute of the :py:mod:`logging` module with the
        value ``level_num``.
    level_num : int
        The numerical value of the new level.
    method_name : str
        The name of the convenience method for both :py:mod:`logging`
        itself and the class returned by
        :py:func:`logging.getLoggerClass` (usually just
        :py:class:`logging.Logger`). If ``method_name`` is not
        specified, ``level_name.lower()`` is used instead.
    if_exists : {_KEEP, _KEEP_WARN, OVERWRITE, OVERWRITE_WARN, RAISE}
        What to do if a level with `level_name` appears to already be
        registered in the :py:mod:`logging` module:

        :py:const:`_KEEP`
            Silently keep the old level as-is.
        :py:const:`_KEEP_WARN`
            Keep the old level around and issue a warning.
        :py:const:`OVERWRITE`
            Silently overwrite the old level.
        :py:const:`OVERWRITE_WARN`
            Overwrite the old level and issue a warning.
        :py:const:`RAISE`
            Raise an error.

        The default is :py:const:`_KEEP_WARN`.
    exc_info : bool
        Default value for the ``exc_info`` parameter of the new method.
    stack_info : bool
        Default value for the ``stack_info`` parameter of the new
        method.

    Examples
    --------
    >>> _AddLoggingLevel('TRACE', logging.DEBUG - 5)
    >>> logging.getLogger(__name__).setLevel("TRACE")
    >>> logging.getLogger(__name__).trace('that worked')
    >>> logging.trace('so did this')
    >>> logging.TRACE
    5

    >>> _AddLoggingLevel('XTRACE', 2, exc_info=True)
    >>> logging.getLogger(__name__).setLevel(logging.XTRACE)
    >>> try:
    >>>     1 / 0
    >>> except:
    >>>     # This line will log the exception
    >>>     logging.getLogger(__name__).xtrace('that failed')
    >>>     # This one will not
    >>>     logging.xtrace('so did this', exc_info=False)

    The ``TRACE`` level can be added using :py:func:`add_trace_level`.
    """
    # This method was inspired by the answers to Stack Overflow post
    # http://stackoverflow.com/q/2183233/2988730, especially
    # http://stackoverflow.com/a/13638084/2988730
    def for_logger_class(self, message, *args, **kwargs):
        if self.isEnabledFor(level_num):
            kwargs.setdefault('exc_info', exc_info)
            kwargs.setdefault('stack_info', stack_info)
            self._log(level_num, message, args, **kwargs)

    def for_logging_module(*args, **kwargs):
        kwargs.setdefault('exc_info', exc_info)
        kwargs.setdefault('stack_info', stack_info)
        logging.log(level_num, *args, **kwargs)

    if not method_name:
        method_name = level_name.lower()

    # The number of items required for a full registration is 4
    items_found = 0
    # Items that are found complete but are not expected values
    items_conflict = 0

    # Lock because logger class and level name are queried and set
    logging._acquireLock()
    try:
        registered_num = logging.getLevelName(level_name)
        logger_class = logging.getLoggerClass()

        if registered_num != 'Level ' + level_name:
            items_found += 1
            if registered_num != level_num:
                if if_exists == _RAISE:
                    # Technically this is not an attribute issue, but for
                    # consistency
                    raise AttributeError(
                        'Level {!r} already registered in logging '
                        'module'.format(level_name)
                    )
                items_conflict += 1

        if hasattr(logging, level_name):
            items_found += 1
            if getattr(logging, level_name) != level_num:
                if if_exists == _RAISE:
                    raise AttributeError(
                        'Level {!r} already defined in logging '
                        'module'.format(level_name)
                    )
                items_conflict += 1

        if hasattr(logging, method_name):
            items_found += 1
            logging_method = getattr(logging, method_name)
            if not callable(logging_method) or \
                    getattr(logging_method, '_original_name', None) != \
                    for_logging_module.__name__:
                if if_exists == _RAISE:
                    raise AttributeError(
                        'Function {!r} already defined in logging '
                        'module'.format(method_name)
                    )
                items_conflict += 1

        if hasattr(logger_class, method_name):
            items_found += 1
            logger_method = getattr(logger_class, method_name)
            if not callable(logger_method) or \
                    getattr(logger_method, '_original_name', None) != \
                    for_logger_class.__name__:
                if if_exists == _RAISE:
                    raise AttributeError(
                        'Method {!r} already defined in logger '
                        'class'.format(method_name)
                    )
                items_conflict += 1

        if items_found > 0:
            # items_found >= items_conflict always
            if (items_conflict or items_found < 4) and \
                    if_exists in (_KEEP_WARN, _OVERWRITE_WARN):
                action = 'Keeping' if if_exists == _KEEP_WARN else 'Overwriting'
                if items_conflict:
                    problem = 'has conflicting definition'
                    items = items_conflict
                else:
                    problem = 'is partially configured'
                    items = items_found
                warnings.warn(
                    'Logging level {!r} {} already ({}/4 items): {}'.format(
                        level_name, problem, items, action)
                )

            if if_exists in (_KEEP, _KEEP_WARN):
                return

        # Make sure the method names are set to sensible values, but
        # preserve the names of the old methods for future verification.
        for_logger_class._original_name = for_logger_class.__name__
        for_logger_class.__name__ = method_name
        for_logging_module._original_name = for_logging_module.__name__
        for_logging_module.__name__ = method_name

        # Actually add the new level
        logging.addLevelName(level_num, level_name)
        setattr(logging, level_name, level_num)
        setattr(logger_class, method_name, for_logger_class)
        setattr(logging, method_name, for_logging_module)
    finally:
        logging._releaseLock()



def SetupLogging(   *,
                AppName:str, 
                Verbose:int = 0, 
                NoDaemon:bool = True, 
                StdErr:bool = False, 
                LogFile:str = '', 
                LogFileInterval:int = 60*60*24,
                LogFileCount:int = 14,
                Quiet:bool = False, 
                ProcInfo:bool = False, 
                ProcInfoModLen:int = 15,
                ProcInfoFuncLen:int = 15,
                LevelType:int = 2,
                MultiProc:bool = False,
                MultiProcLen:int = 15,
                MultiThread:bool = False,
                MultiThreadLen:int = 15,
                StackOnDebug:str = 'NONE',
                StackDepth:int = 5,
                DebugIp:str = '127.0.0.1',
                DebugPort:int = 0,
                DebugCacheSize:int = 100,
                NoReset:bool = False) -> PortLogServer:
    """Creates a defined Log-setting with rich options

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

    LevelType (int, optional): Format of LevelInfo. 0=None, 1=Number, 2=Name, 3=Both. 
                                Defaults to 2.

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

    DebugPort (int, optional): If 0 no debug-server is started. Else the value has to be 
                                between 1024 and 65535. A log-server is started on 'DebugIp' 
                                at port 'DebugPort'. 
                                It is possible to connect to this port (e.g with telnet) to 
                                receive ALL log-messages from this program. ALL means really
                                all, no mather which loglevel is set. This output also 
                                includes all possible information about process, thread, 
                                module and function. The stacktrace ('StackOnDebug') is also
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
                                
    DebugIp (str, optional): The IP-address to bind to. This address must exist on the host 
                                this program is running. '0.0.0.0' for 'all IPs' is also 
                                valid. Only examined if 'DebugPort' > 0. 
                                Defaults to '127.0.0.1',
                                
    DebugCacheSize (int, optional): Only used if 'DebugPort' > 0. This is the number of 
                                log-messages cached for use at a new connection to the 
                                server. So if someone connects to the server he receives the
                                last 'DebugCacheSize' log messages and after them all new 
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

                        
                        
    """
    
    if not NoReset:
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)


# Add the 3 additional log-level
    _AddLoggingLevel('TRACE', logging.DEBUG -5, 'trace')
    _AddLoggingLevel('MSG', logging.WARNING - 1, 'msg')
    _AddLoggingLevel('STATUS', logging.ERROR - 1, 'status')

# Check Port option
    try:
        DebugPort = int(DebugPort)
    except:
        raise ValueError(f"SetupLogging 'DebugPort' can't be converted to an integer")
    if DebugPort < 0:
        DebugPort = 0
# Check Len options
    try:
        ProcInfoModLen = int(ProcInfoModLen)
    except:
        raise ValueError(f"SetupLogging 'ProcInfoModLen' can't be converted to an integer")
    if ProcInfoModLen < 0:
        raise ValueError(f"SetupLogging 'ProcInfoModLen' can't be negative")

    try:
        ProcInfoFuncLen = int(ProcInfoFuncLen)
    except:
        raise ValueError(f"SetupLogging 'ProcInfoFuncLen' can't be converted to an integer")
    if ProcInfoModLen < 0:
        raise ValueError(f"SetupLogging 'ProcInfoFuncLen' can't be negative")

    try:
        MultiProcLen = int(MultiProcLen)
    except:
        raise ValueError(f"SetupLogging 'MultiProcLen' can't be converted to an integer")
    if ProcInfoModLen < 0:
        raise ValueError(f"SetupLogging 'MultiProcLen' can't be negative")

    try:
        MultiThreadLen = int(MultiThreadLen)
    except:
        raise ValueError(f"SetupLogging 'MultiThreadLen' can't be converted to an integer")
    if ProcInfoModLen < 0:
        raise ValueError(f"SetupLogging 'MultiThreadLen' can't be negative")

    try:
        DebugCacheSize = int(DebugCacheSize)
    except:
        raise ValueError(f"SetupLogging 'DebugCacheSize' can't be converted to an integer")
    if ProcInfoModLen < 0:
        raise ValueError(f"SetupLogging 'DebugCacheSize' can't be negative")
    
    
# Add the Filter to implement stack-traces
    if not isinstance(StackOnDebug, str):
        raise ValueError(f"SetupLogging 'StackOnDebug' is not a string")
    wTxt = StackOnDebug.upper()
    if wTxt =='ERROR':
        Sd = logging.ERROR
    elif wTxt =='STATUS':
        Sd = logging.STATUS
    elif wTxt =='WARNING':
        Sd = logging.WARNING
    elif wTxt == 'MSG':
        Sd = logging.MSG
    elif wTxt == 'INFO':
        Sd = logging.INFO
    elif wTxt == 'DEBUG':
        Sd = logging.DEBUG
    elif wTxt == 'TRACE':
        Sd = logging.TRACE
    else:
        Sd = -1

    logging.getLogger().addFilter(_AddStackContextFilter(StackDepth, Sd))
    
    if not NoDaemon:  # Ausgabe auf StdErr macht als Daemon keinen Sinn
        StdErr = False

    if Quiet:  # Wenn Quiet angegeben ist macht Verbose keinen Sinn
        Verbose = -1

    if Verbose == 0:  # Default
        LogLevel = logging.STATUS
    elif Verbose == 1:  # Mit Meldungen
        LogLevel = logging.MSG
    elif Verbose == 2:  # Mit Infos
        LogLevel = logging.INFO
    elif Verbose == 3:  # Mit debug infos
        LogLevel = logging.DEBUG
    elif Verbose >= 4:  # Mit itrace infos
        LogLevel = logging.TRACE
    else:  # Quiet
        LogLevel = logging.ERROR
        
    try:
        LevelType = int(LevelType)
    except:
        raise ValueError(f"SetupLogging 'LevelType' can't be converted to an integer")
    if LevelType == 1:
        ShowLevel = '%(levelno)02d '
    elif LevelType == 2:
        ShowLevel = '%(levelname)7s '
    elif LevelType == 3:
        ShowLevel = '%(levelno)02d=%(levelname)7s '
    else:
        ShowLevel = ''
    
    if ProcInfo:
        AddPar = ''
        if MultiProc:
            if MultiProcLen == 0: 
                AddPar += '%(processName)s'
            else:
                AddPar += f"%(processName){MultiProcLen}s"
        if MultiThread:
            if AddPar != '':
                AddPar += ':'
            if MultiThreadLen == 0:
                AddPar += '%(threadName)s'
            else:
                AddPar += f"%(threadName)-{MultiThreadLen}s"
        if ProcInfoModLen == 0:
            AddPar += ' %(module)s'
        else:
            AddPar += f" %(module){ProcInfoModLen}s"
        if ProcInfoFuncLen == 0:
            AddPar += ':%(funcName)s:'
        else:
            AddPar += f":%(funcName)-{ProcInfoFuncLen}s:"
        AddPar += '%(lineno)4d'
    else:
        AddPar = ''
    
    if LogFile != '':
        Format = f"%(asctime)s - {AppName} {ShowLevel}{AddPar} - %(message)s%(stack)s"
        FileLogHand = logging.handlers.TimedRotatingFileHandler(LogFile, when = 'S',interval = LogFileInterval, backupCount = LogFileCount)

        FileLogHand.setLevel(LogLevel)
        Formatter = logging.Formatter(Format)
        FileLogHand.setFormatter(Formatter)
        logging.getLogger().addHandler(FileLogHand)

        # logging.basicConfig(handlers = [FileLogHand], level = LogLevel, format = Format)
        FileLogHand.doRollover()
    elif StdErr:
        if AddPar == '' and ShowLevel == '':
            Format = f"%(asctime)s %(message)s%(stack)s"
        else:
            Format = f"%(asctime)s {ShowLevel}{AddPar} - %(message)s%(stack)s"

        StdErrHandler = logging.StreamHandler()
        StdErrHandler.setLevel(LogLevel)
        Formatter = logging.Formatter(Format)
        StdErrHandler.setFormatter(Formatter)
        logging.getLogger().addHandler(StdErrHandler)
        
#        logging.basicConfig(stream = sys.stderr, level = LogLevel, format = Format)
    else:
        Format = f"{AppName} {ShowLevel}{AddPar} - %(message)s%(stack)s" 
        SysLogHand = logging.handlers.SysLogHandler(address = '/dev/log')

        SysLogHand.setLevel(LogLevel)
        Formatter = logging.Formatter(Format)
        SysLogHand.setFormatter(Formatter)
        logging.getLogger().addHandler(SysLogHand)
        
#        logging.basicConfig(handlers = [SysLogHand], level = LogLevel, format = Format)
    logging.getLogger().setLevel(1)

    LogServer = DummyPortLogServer()
    if DebugPort != 0:
        AddPar = ''
        if MultiProcLen == 0: 
            AddPar += '%(processName)s'
        else:
            AddPar += f"%(processName){MultiProcLen}s"
        if AddPar != '':
            AddPar += ':'
        if MultiThreadLen == 0:
            AddPar += '%(threadName)s'
        else:
            AddPar += f"%(threadName)-{MultiThreadLen}s"
        if ProcInfoModLen == 0:
            AddPar += ' %(module)s'
        else:
            AddPar += f" %(module){ProcInfoModLen}s"
        if ProcInfoFuncLen == 0:
            AddPar += ':%(funcName)s:'
        else:
            AddPar += f":%(funcName)-{ProcInfoFuncLen}s:"
        AddPar += '%(lineno)4d'
        ShowLevel = '%(levelname)7s '
        Format = f"%(asctime)s {ShowLevel}{AddPar} - %(message)s%(stack)s"
        LogServer = PortLogServer(host=DebugIp,port=DebugPort,queue=LogQueue,logsize=DebugCacheSize,format=Format)
        qh = PortLogQueueHandler(LogServer, LogQueue)
        qh.setLevel(1)
        logging.getLogger().addHandler(qh)
        LogServer.Run()

    return LogServer
        
        
LogQueue = multiprocessing.Queue()

_AddLoggingLevel('TRACE', logging.DEBUG -5, 'trace')
_AddLoggingLevel('MSG', logging.WARNING - 1, 'msg')
_AddLoggingLevel('STATUS', logging.ERROR - 1, 'status')

error = partial(logging.log, logging.ERROR)
"""Error logging function
    usage: LogP.error("Msg")"""

warning = partial(logging.log, logging.WARNING)
"""Warning logging function
    usage: LogP.warning("Msg")"""

info = partial(logging.log, logging.INFO)
"""Info logging function
    usage: LogP.info("Msg")"""

msg = partial(logging.log,logging.MSG)
"""Msg logging function
    usage: LogP.msg("Msg")"""

status = partial(logging.log,logging.STATUS)
"""Status logging function
    usage: LogP.status("Msg")"""

trace = partial(logging.log,logging.TRACE)
"""Trace logging function
    usage: LogP.trace("Msg")"""

debug = partial(logging.log,logging.DEBUG)
"""Debug logging function
    usage: LogP.debug("Msg")"""

log = partial(logging.log)
"""Log logging function
    usage: LogP.log(level,"Msg")"""


if __name__ == '__main__':
    import LogP
    import LogP as XXLogP
    
    
    def abc():
        LogP.error('Error')
        LogP.status('Status')
        LogP.warning('Warning')
        LogP.msg('Msg')
        LogP.info('Info')
        LogP.debug('Debug')
        XXLogP.trace('Trace')
    
    
    def main():
        MyParam= {}
        MyParam['Verbose'] = 4
        MyParam['StdErr'] = True
        MyParam['NoDaemon'] = True
        MyParam['Quiet'] = False
        MyParam['LogFile'] = ''
        MyParam['ProcInfo'] = True
    
    #    MyParam['LogFile'] = './TheLog.log'
        AppName = "LogP"
    
    
        LogServer = LogP.SetupLogging(AppName = AppName, 
                        Verbose = MyParam['Verbose'], 
                        StdErr = MyParam['StdErr'], 
                        NoDaemon = MyParam['NoDaemon'], 
                        Quiet = MyParam['Quiet'],
                        LogFile = MyParam['LogFile'],
                        ProcInfo = False,
#                        StackOnDebug = "debug",
#                        StackDepth=2,
                        LevelType = 0,
                        MultiProc = False, 
                        MultiThread = False,
                        ProcInfoModLen=5,
                        DebugPort=65432
                        ) 
    
        LogP.error('Error')
        LogP.warning('Warning')
        LogP.info('Info')
        LogP.msg('Msg')
        LogP.status('Status')
        LogP.trace('Trace')
        LogP.debug('Debug')
        abc()
        LogServer.Stop()
        LogServer.Join(2)
        LogServer.Kill()
        
        LogServer = LogP.SetupLogging(AppName = AppName, 
                        Verbose = MyParam['Verbose'], 
                        StdErr = MyParam['StdErr'], 
                        NoDaemon = MyParam['NoDaemon'], 
                        Quiet = MyParam['Quiet'],
                        LogFile = MyParam['LogFile'],
                        LevelType=3,
                        ProcInfo = True,
                        MultiProc = False, 
                        MultiThread = False,
                        ProcInfoModLen=15,
                        ProcInfoFuncLen=15,
                        DebugPort=65432
                        ) 
    
        LogP.error('Error')
        LogP.warning('Warning')
        LogP.info('Info')
        LogP.msg('Msg')
        LogP.status('Status')
        LogP.trace('Trace')
        LogP.debug('Debug')
        abc()
        LogServer.Stop()
        LogServer.Join(2)
        LogServer.Kill()
    
    main()
