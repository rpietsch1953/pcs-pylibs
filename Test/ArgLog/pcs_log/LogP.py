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
# from PortLogServer import PortLogServer, PortLogQueueHandler, DummyPortLogServer
import multiprocessing
from functools import partial
import socket
import time
import sys
import signal
import logging
import logging.config
import multiprocessing
from ctypes import c_bool
import netifaces
import setproctitle

_KEEP = 'keep'
_KEEP_WARN = 'keep-warn'
_RAISE = 'raise'
_OVERWRITE_WARN = 'overwrite-warn'
_LOGSTATUS = logging.ERROR - 1

Run = multiprocessing.Value(c_bool, True)

class DummyPortLogServer():
    def __init__(self, *args, **kwargs):
        """The dummy-version of the 'PortLogServer'-class
        This class is used to return it to a user if no real Log-server is requested.
        So the programmer can call the functions without the need to question if
        a real server is running. All functions are No-Ops.
        """        
        pass
    
    def Run(self, *args, **kwargs) -> None:
        pass
    
    def Stop(self, *args, **kwargs) -> None:
        pass
    
    @property
    def RunFlag(self) -> bool:
        return False
    
    @property
    def Name(self) -> str:    
        return ''
    
    @property
    def Port(self) -> int:
        return 0

    @property
    def IsAlive(self) -> bool:
        return False
    
    def PollRestart(self) -> None:
        pass
    
    def Kill(self) -> None:
        pass
    
    def Join(self, *args, **kwargs) -> None:
        pass
        

class PortLogServer():
    def __init__(self, *,   # only key-word arguments from here on
                 host:str = '127.0.0.1', 
                 port:int = 0, 
                 name:str = '', 
                 queue:multiprocessing.Queue = None, 
                 logsize:int = 0,
                 format:str = '') -> None:
        """Send the messages from the input-Queue to a tcp-client
        on the defined address and port.

        Args:
            port (int, optional): The port to use (1024 to 65535). Defaults to 0.
            name (str, optional): The process-name of this class. Defaults to ''.
            queue (multiprocessing.Queue, optional): The input queue. Defaults to None.
            logsize (int, optional): if >0 logsize messages are buffered and send to the client on connection. Defaults to 0.

        Raises:
            ValueError: if invalid arguments are given.
        """       
        self.__RunFlag = multiprocessing.Value(c_bool, True)
        self.__CanReload = True         # prevent restarting after Stop, Join or Kill
        
        self.__FormatStr = format.strip()
        self.__Formatter = None
        if self.__FormatStr != '':
            self.__Formatter = logging.Formatter(self.__FormatStr)
            
        self.__Name = name.strip()
        #
        # Logging cache
        #
        try:
            logsize = int(logsize)
            if logsize < 0:
                logsize = 0
        except:
            logsize = 0
        self.__LogSize = logsize
        self.__LogCache = []
        #
        # Ip addr for server
        #
        if not isinstance(host, str):
            raise ValueError(f"{__class__.__name__} host (type={type(host)}) is not a string - object")
        if host.lower() == 'localhost':
            host = '127.0.0.1'
        if not host in self.__MyValidIps:
            raise ValueError(f"{__class__.__name__} host '{host}' is not an valid IP of this computer")
        self.__Host = host
        #
        # the input queue
        #
        if queue is not None:
            if not isinstance(queue, multiprocessing.queues.Queue):
                raise ValueError(f"{__class__.__name__} queue (type={type(queue)}) is not a multiprocessing.Queue - object")
        self.__Queue = queue
        #
        # set the port
        #
        try:
            port = int(port)
        except:
            port = 0
        if port < 1024 or port > 65535:
            raise ValueError(f"{__class__.__name__} port must be between 1024 and 65535")
        self.__Port = port
        
        self.__Connections = {}         # clear connection-dict
        self.__ReaderProcess = None     # the reader process
    
    def Run(self, *,  
            name:str = '', 
            queue:multiprocessing.Queue = None) -> None:
        """Starts the reader-process

        Args:
            name (str, optional): Can overwrite the process-name of this instance. Defaults to ''.
            queue (multiprocessing.Queue, optional): can overwrite the input queue of this instance. 
                        If not given the name from the creation is used Defaults to None.

        Raises:
            ValueError: if invalid arguments are given.
        """        
        if queue is not None:
            if not isinstance(queue, multiprocessing.queues.Queue):
                raise ValueError(f"{__class__.__name__}.Run queue (type={type(queue)}) is not a multiprocessing.Queue - object")
            self.__Queue = queue
        if self.__Queue is None:
            raise ValueError(f"{__class__.__name__} .Run queue (type={type(self.__Queue)}) is not a multiprocessing.Queue - object")
        name = name.strip()
        if name == '':
            name = 'PortLogServer'
        self.__Name = name
        self.__RunFlag = True
        self.__StartReader()
        
    
    def Stop(self) -> None:
        """Stop the reader-process
        """
        self.__RunFlag = False
        logging.log(_LOGSTATUS,"Stop Log-server")
        self.__Queue.put_nowait('DONE')
        self.__CanReload = False
    
    @property
    def RunFlag(self) -> bool:
        """Return True if the process is running
        """        
        return self.__RunFlag
    
    @property
    def Name(self) -> str:
        """Return the process-name of this instance
        """
        return self.__Name
    
    @property
    def Port(self) -> int:
        """Return the port-number of this instance
        """
        return self.__Port
        
    @property
    def __MyValidIps(self) -> list:
        """Return a list of all valid IPs of this computer
        """
        Erg = []
        for interface in netifaces.interfaces():
            AddrDict = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in AddrDict:
                for link in AddrDict[netifaces.AF_INET]:
                    Erg.append(link['addr'])
        if len(Erg) != 0:
            Erg.append('0.0.0.0')
        return Erg
         
    def __TermConnection(self, Client: str) -> None:
        """Terminate a connection
        """
        # try:
        #     SendBuff = 'Quit\n'.encode('utf-8')
        #     QuitBuff = bytearray(b'\x00')
        #     self.__Connections[Client].sendall(SendBuff)
        #     self.__Connections[Client].sendall(QuitBuff)
        # except:
        #     pass
        self.__Connections[Client].close()
        logging.log(_LOGSTATUS,f'reader_proc disconnect client {Client}')
        self.__Connections[Client] = None

    def __CollectClients(self) -> None:
        """Clear dead connections from dict
        """
        KillConnection = []
        for Client, Connection in self.__Connections.items():
            if Connection is None:
                KillConnection.append(Client)
        for Client in KillConnection:
            del self.__Connections[Client]
            
    def __TermHandler(self, signum, frame):
        """The term-handler for this process
        """
        logging.warning(f'reader_proc - Termination handler invoked with signal {signum}')
        self.__RunFlag = False
        
    def __StartReader(self) -> None:
        """Start the reader-process
        """
        if self.__ReaderProcess is not None:
            if self.__ReaderProcess.is_alive():
                return
            e = self.__ReaderProcess.exitcode
        
        self.__ReaderProcess = multiprocessing.Process(target=self.__ReaderProc, name=self.__Name)
        self.__ReaderProcess.daemon = True
        self.__RunFlag = True
        self.__ReaderProcess.start()  # Launch self.__ReaderProcess() as another proc
        logging.log(_LOGSTATUS,"Start Log-server at {self.__Host}:{self.__Port}")
        return
    
    @property
    def IsAlive(self) -> bool:
        """Returnm True if the process is alive
        """
        Ret = False
        try:
            Ret = self.__ReaderProcess.is_alive()
        except:
            pass
        return Ret
    
    def PollRestart(self) -> None:
        """Restart the process if it is not alive
        """
        if self.__CanReload:
            if not self.IsAlive:
                self.Run()
        
    def Kill(self) -> None:
        """Kill this process
        """
        self.__CanReload = False
        try:
            self.__ReaderProcess.kill()
        except:
            pass
    
    def Join(self, Timeout: float = None) -> None:
        """Join this process
        If the optional argument timeout is None (the default), the method blocks until 
        the process whose join() method is called terminates. If timeout is a positive 
        number, it blocks at most timeout seconds. Note that the method returns None 
        if its process terminates or if the method times out. 
        """
        self.__CanReload = False
        try:
            self.__ReaderProcess.join(Timeout)
        except:
            pass
    
    def __ReaderProc(self) -> None:
        """Read from the queue; this spawns as a separate Process"""
            
        setproctitle.setproctitle(multiprocessing.current_process().name)
        logging.log(_LOGSTATUS,f'reader_proc - Starting')
        signal.signal(signal.SIGINT, self.__TermHandler)   # Setze Signalhandler
        signal.signal(signal.SIGTERM, self.__TermHandler)
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM | socket.SOCK_NONBLOCK)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT,1)
        server.setblocking(False)
        IsOk = False
        for i in range(10):
            if not self.__RunFlag:
                return 0
            try:
                server.bind((self.__Host, self.__Port))
                server.setblocking(False)
                server.listen()
                IsOk = True
                break
            except:
                logging.warning(f'reader_proc - Can not connect')
                time.sleep(1)
        if not IsOk:
            self.__RunFlag = False
            return
        server.listen(5)

        while self.__RunFlag:
            try:
                Connection, Address = server.accept()
                Connection.setblocking(False)
                ClientStr = f"{Address[0]}:{Address[1]}"
                logging.log(_LOGSTATUS,f'reader_proc connection from {ClientStr}')
                self.__Connections[ClientStr] = Connection
                for l in self.__LogCache:
                    try:
                        Connection.sendall(l.encode('utf-8'))
                    except:
                        self.__TermConnection(Client)
            except :
                pass
            if not self.__RunFlag:
                break
            for Client, Connection in self.__Connections.items():
                if not self.__RunFlag:
                    break
                if Connection is not None:
                    try:
                        message = None
                        message = Connection.recv(4096) # .decode('utf-8')
                        if message[0] == 0xFF and message[1] == 0xF4:
                            self.__TermConnection(Client)
                            break
                        if len(message) != 0:
                            try:
                                m = message.decode('utf-8').strip()
                                if m == 'q' or m == 'Q':
                                    self.__TermConnection(Client)
                                    break
                            except:
                                continue
                    except BlockingIOError:
                        continue
                    except Exception as exc:
                        logging.warning(f'reader_proc exception - {exc}')
            self.__CollectClients()        
            try:
                Msg = self.__Queue.get(False,1)
                if isinstance(Msg, logging.LogRecord):
                   if self.__Formatter is not None:
                       Msg =  self.__Formatter.format(Msg) + '\n'
                   else:
                       Msg = None
                # print(type(Msg))
            except:
                Msg = None
            if Msg is not None:
                if Msg == "DONE":
                    break
                if self.__LogSize != 0: 
                    self.__LogCache.append(Msg)
                    if len(self.__LogCache) > self.__LogSize:
                        self.__LogCache.pop(0)
                for Client, Connection in self.__Connections.items():
                    if not self.__RunFlag:
                        break
                    try:
                        if Connection is not None:
                            Connection.sendall(Msg.encode('utf-8'))
                    except:
                        self.__TermConnection(Client)
                self.__CollectClients()

        for Client, Connection in self.__Connections.items():
            self.__TermConnection(Client)
        self.__CollectClients()
        server.close()
        self.__RunFlag = False
        logging.log(_LOGSTATUS,f'reader_proc - Terminating')
    
        
class PortLogQueueHandler(logging.handlers.QueueHandler):
    """
    
    """
    def __init__(self, ProcClass:PortLogServer, *args, **kwargs):
        """A queue-handler that allowes the automatic restart of the Log-server

        Args:
            ProcClass (PortLogServer): An instance of the listening PortLogServer.
                                        Needet to automatically restart if the
                                        server is terminated. All other parametrs
                                        look at the documentation of 
                                        'logging.handlers.QueueHandler'
        """        
        super().__init__(*args, **kwargs)
        self.__ProcClass = ProcClass
        
    def enqueue(self, record):
        """Overwritten enqueue function of the 'logging.handlers.QueueHandler' class.
        """        
        self.__ProcClass.PollRestart()
        super().enqueue(record)
        

class _AddStackContextFilter(logging.Filter):
    def __init__(self, trim_amount: int = 5, below_level: int = -1, is_syslog: bool = False):
        """Class to prepaire the "stack"-variable within logrecord

        Args:
            trim_amount (int, optional): Maximum number of stack-lines to show. Defaults to 5.
            below_level (int, optional): Log-leven below or equal a stacktrace is shown. Defaults to -1 => disabled.
        """        
        self.trim_amount = trim_amount
        self.below_level = below_level
        self.is_syslog = is_syslog
        
    def IsLast(self,s):
        Such = '\n    root.log(level, msg, *args, **kwargs)\n'
        return Such in s        

    def filter(self, record):
        import traceback
        if self.is_syslog:
            Delim = '\u21B2'
        else:
            Delim = '\n'

        if record.levelno <= self.below_level:
            wStack = traceback.format_stack()
            ResList = []
            for r in wStack:
                s = str(r)
                if self.IsLast(s):
                    break
                ResList.append(s.replace('\n', Delim))
            
            record.stack = Delim + ''.join(ResList[0-self.trim_amount:])
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
                LogPath:str = '', 
                LogFileInterval:int = 60*60*24,
                LogFileCount:int = 14,
                Quiet:bool = False, 
                LogProcInfo:bool = False, 
                LogProcInfoModLen:int = 15,
                LogProcInfoFuncLen:int = 15,
                LogLevelType:int = 2,
                LogMultiProc:bool = False,
                LogMultiProcLen:int = 15,
                LogMultiThread:bool = False,
                LogMultiThreadLen:int = 15,
                LogStackOnDebug:str = 'NONE',
                LogStackDepth:int = 5,
                LogDebugIp:str = '127.0.0.1',
                LogDebugPort:int = 0,
                LogDebugCacheSize:int = 100,
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
        LogDebugPort = int(LogDebugPort)
    except:
        raise ValueError(f"SetupLogging 'LogDebugPort' can't be converted to an integer")
    if LogDebugPort < 0:
        LogDebugPort = 0
# Check Len options
    try:
        LogProcInfoModLen = int(LogProcInfoModLen)
    except:
        raise ValueError(f"SetupLogging 'LogProcInfoModLen' can't be converted to an integer")
    if LogProcInfoModLen < 0:
        raise ValueError(f"SetupLogging 'LogProcInfoModLen' can't be negative")

    try:
        LogProcInfoFuncLen = int(LogProcInfoFuncLen)
    except:
        raise ValueError(f"SetupLogging 'LogProcInfoFuncLen' can't be converted to an integer")
    if LogProcInfoFuncLen < 0:
        raise ValueError(f"SetupLogging 'LogProcInfoFuncLen' can't be negative")

    try:
        LogMultiProcLen = int(LogMultiProcLen)
    except:
        raise ValueError(f"SetupLogging 'LogMultiProcLen' can't be converted to an integer")
    if LogProcInfoModLen < 0:
        raise ValueError(f"SetupLogging 'LogMultiProcLen' can't be negative")

    try:
        LogMultiThreadLen = int(LogMultiThreadLen)
    except:
        raise ValueError(f"SetupLogging 'LogMultiThreadLen' can't be converted to an integer")
    if LogProcInfoModLen < 0:
        raise ValueError(f"SetupLogging 'LogMultiThreadLen' can't be negative")

    try:
        LogDebugCacheSize = int(LogDebugCacheSize)
    except:
        raise ValueError(f"SetupLogging 'LogDebugCacheSize' can't be converted to an integer")
    if LogProcInfoModLen < 0:
        raise ValueError(f"SetupLogging 'LogDebugCacheSize' can't be negative")
    
    
# Add the Filter to implement stack-traces
    if not isinstance(LogStackOnDebug, str):
        raise ValueError(f"SetupLogging 'LogStackOnDebug' is not a string")
    wTxt = LogStackOnDebug.upper()
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
    IsSyslog = False
    if LogPath == '' and not StdErr:
        IsSyslog = True
    logging.getLogger().addFilter(_AddStackContextFilter(trim_amount = LogStackDepth,below_level = Sd, is_syslog = IsSyslog))
    
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
        LogLevelType = int(LogLevelType)
    except:
        raise ValueError(f"SetupLogging 'LogLevelType' can't be converted to an integer")
    if LogLevelType == 1:
        ShowLevel = '%(levelno)02d '
    elif LogLevelType == 2:
        ShowLevel = '%(levelname)7s '
    elif LogLevelType == 3:
        ShowLevel = '%(levelno)02d=%(levelname)7s '
    else:
        ShowLevel = ''
    
    if LogProcInfo:
        AddPar = ''
        if LogMultiProc:
            if LogMultiProcLen == 0: 
                AddPar += '%(processName)s'
            else:
                AddPar += f"%(processName){LogMultiProcLen}s"
        if LogMultiThread:
            if AddPar != '':
                AddPar += ':'
            if LogMultiThreadLen == 0:
                AddPar += '%(threadName)s'
            else:
                AddPar += f"%(threadName)-{LogMultiThreadLen}s"
        if LogProcInfoModLen == 0:
            AddPar += ' %(module)s'
        else:
            AddPar += f" %(module){LogProcInfoModLen}s"
        if LogProcInfoFuncLen == 0:
            AddPar += ':%(funcName)s:'
        else:
            AddPar += f":%(funcName)-{LogProcInfoFuncLen}s:"
        AddPar += '%(lineno)4d'
    else:
        AddPar = ''
    
    if LogPath != '':
        Format = f"%(asctime)s - {AppName} {ShowLevel}{AddPar} - %(message)s%(stack)s"
        FileLogHand = logging.handlers.TimedRotatingFileHandler(LogPath, when = 'S',interval = LogFileInterval, backupCount = LogFileCount)

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
    if LogDebugPort != 0:
        AddPar = ''
        if LogMultiProcLen == 0: 
            AddPar += '%(processName)s'
        else:
            AddPar += f"%(processName){LogMultiProcLen}s"
        if AddPar != '':
            AddPar += ':'
        if LogMultiThreadLen == 0:
            AddPar += '%(threadName)s'
        else:
            AddPar += f"%(threadName)-{LogMultiThreadLen}s"
        if LogProcInfoModLen == 0:
            AddPar += ' %(module)s'
        else:
            AddPar += f" %(module){LogProcInfoModLen}s"
        if LogProcInfoFuncLen == 0:
            AddPar += ':%(funcName)s:'
        else:
            AddPar += f":%(funcName)-{LogProcInfoFuncLen}s:"
        AddPar += '%(lineno)4d'
        ShowLevel = '%(levelname)7s '
        Format = f"%(asctime)s {ShowLevel}{AddPar} - %(message)s%(stack)s"
        LogServer = PortLogServer(host=LogDebugIp,port=LogDebugPort,queue=LogQueue,logsize=LogDebugCacheSize,format=Format)
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
        MyParam['LogPath'] = ''
        MyParam['LogProcInfo'] = True
    
    #    MyParam['LogPath'] = './TheLog.log'
        AppName = "LogP"
    
    
        LogServer = LogP.SetupLogging(AppName = AppName, 
                        Verbose = MyParam['Verbose'], 
                        StdErr = MyParam['StdErr'], 
                        NoDaemon = MyParam['NoDaemon'], 
                        Quiet = MyParam['Quiet'],
                        LogPath = MyParam['LogPath'],
                        LogProcInfo = False,
#                        LogStackOnDebug = "debug",
#                        LogStackDepth=2,
                        LogLevelType = 0,
                        LogMultiProc = False, 
                        LogMultiThread = False,
                        LogProcInfoModLen=5,
                        LogDebugPort=65432
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
                        LogPath = MyParam['LogPath'],
                        LogLevelType=3,
                        LogProcInfo = True,
                        LogMultiProc = False, 
                        LogMultiThread = False,
                        LogProcInfoModLen=15,
                        LogProcInfoFuncLen=15,
                        LogDebugPort=65432
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
