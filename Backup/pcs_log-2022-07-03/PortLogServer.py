#!/usr/bin/env python3
# vim: expandtab:ts=4:sw=4:noai


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
    
    def Join(self, Timeout: float) -> None:
        """Join this process
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
        
    
      
    
    
    
##############################################################
# Test if called as standalone program
##############################################################

if __name__ == '__main__':
    LogQueue = multiprocessing.Queue()    # create the Queue 

    HOST = "127.0.0.1"  # Standard loopback interface Address (localhost)
    #HOST = "0.0.0.0"
    PORT = 65432  # Port to listen on (non-privileged ports are > 1023 and < 65536)

    #-------------------------------------
    # Rückruffunktion Abbruch-Signale
    #-------------------------------------
    def TermHandler(signum, frame):
        global Run
        logging.warning(f'main - Termination handler invoked with signal {signum}')
        Run = False
    
    signal.signal(signal.SIGINT, TermHandler)   # Setze Signalhandler
    signal.signal(signal.SIGTERM, TermHandler)

    # Initialisiere das Log-Format
    AddPar = ''
    AddPar += '%(levelname)7s '
    AddPar += '%(processName)20s'
    AddPar += ':'
    AddPar += '%(threadName)-15s'
    AddPar += ' %(module)15s:%(funcName)-15s:%(lineno)4d'
    Format = f"%(asctime)s {AddPar} - %(message)s"
    logging.basicConfig(stream = sys.stderr, level = 1, format = Format)

#     qh = logging.handlers.QueueHandler(LogQueue)
#     qh.setLevel(1)
# #    logging.getLogger().setLevel(logging.DEBUG)
#     logging.getLogger().addHandler(qh)

    # setze den eigenen Process-Namen
    multiprocessing.current_process().name = 'TelnetLogger-Main'
    setproctitle.setproctitle('TelnetLogger-Main')

    # PortLogger anlegen
    MyClass = PortLogServer(host = HOST, port = PORT, name = 'Test-PortLogServer', queue = LogQueue,logsize=100,format = Format)
    MyClass.Run()   # und starten
    
    qh = PortLogQueueHandler(MyClass, LogQueue)
    qh.setLevel(1)
    logging.getLogger().addHandler(qh)

    i = 0
    while Run:
        i += 1
        # MyClass.PollRestart()   # Portlogger prüfen und wenn notwendig neu starten
        logging.debug(f"{i}")
#        LogQueue.put(f"{i}\n")  # Log-Messages senden
        if i == 6:              # probeweise neu starten
            LogQueue.put("DONE")
        time.sleep(0.3)
    LogQueue.put("DONE")        # end-signal senden
    MyClass.Join(2)             # auf Ende warten
    if MyClass.IsAlive:         # ist noch aktiv?
        logging.warning(f'main - kill reader')
        time.sleep(2)
        MyClass.Kill()          # Kill hart
        
    logging.info(f'main - Terminating')
    
    
