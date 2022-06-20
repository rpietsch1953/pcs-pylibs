#!/usr/bin/env python3
# vim: expandtab:ts=4:sw=4:noai

import logging
import logging.config
import time
import os
import sys

from functools import partial
import LogP

KEEP = 'keep'
KEEP_WARN = 'keep-warn'

class AddStackContextFilter(logging.Filter):
    def __init__(self, trim_amount: int = 5, below_level: int = -1):
        """Class to prepaire the "stack"-variable within logrecord

        Args:
            trim_amount (int, optional): Maximum number of stack-lines to show. Defaults to 5.
            below_level (int, optional): Log-leven below or equal a stacktrace is shown. Defaults to -1 => disabled.
        """        
        self.trim_amount = trim_amount
        self.below_level = below_level
        
    def filter(self, record):
        import traceback
        if record.levelno <= self.below_level:
            record.stack = '\n' + ''.join(
                str(row) for row in traceback.format_stack()[:-self.trim_amount]
                )
        else:
            record.stack = ''
        return True

def add_logging_level(level_name, level_num, method_name=None,
                      if_exists=KEEP, *, exc_info=False, stack_info=False):
    """
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
    if_exists : {KEEP, KEEP_WARN, OVERWRITE, OVERWRITE_WARN, RAISE}
        What to do if a level with `level_name` appears to already be
        registered in the :py:mod:`logging` module:

        :py:const:`KEEP`
            Silently keep the old level as-is.
        :py:const:`KEEP_WARN`
            Keep the old level around and issue a warning.
        :py:const:`OVERWRITE`
            Silently overwrite the old level.
        :py:const:`OVERWRITE_WARN`
            Overwrite the old level and issue a warning.
        :py:const:`RAISE`
            Raise an error.

        The default is :py:const:`KEEP_WARN`.
    exc_info : bool
        Default value for the ``exc_info`` parameter of the new method.
    stack_info : bool
        Default value for the ``stack_info`` parameter of the new
        method.

    Examples
    --------
    >>> add_logging_level('TRACE', logging.DEBUG - 5)
    >>> logging.getLogger(__name__).setLevel("TRACE")
    >>> logging.getLogger(__name__).trace('that worked')
    >>> logging.trace('so did this')
    >>> logging.TRACE
    5

    >>> add_logging_level('XTRACE', 2, exc_info=True)
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
                if if_exists == RAISE:
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
                if if_exists == RAISE:
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
                if if_exists == RAISE:
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
                if if_exists == RAISE:
                    raise AttributeError(
                        'Method {!r} already defined in logger '
                        'class'.format(method_name)
                    )
                items_conflict += 1

        if items_found > 0:
            # items_found >= items_conflict always
            if (items_conflict or items_found < 4) and \
                    if_exists in (KEEP_WARN, OVERWRITE_WARN):
                action = 'Keeping' if if_exists == KEEP_WARN else 'Overwriting'
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

            if if_exists in (KEEP, KEEP_WARN):
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



def SetupLogging(   AppName: str, 
                    Verbose: int = 0, 
                    NoDaemon: bool = True, 
                    StdErr: bool = False, 
                    LogFile: str = '', 
                    Quiet: bool = False, 
                    ProcInfo: bool = False, 
                    LevelInfo: bool = True, 
                    LevelType: int = 2,
                    MultiProc: bool = False, 
                    MultiThread: bool = False,
                    StackOnDebug: str = 'NONE',
                    StackDepth: int = 5,
                    NoReset: bool = False):
    """Erzeugt eine definierte Log-Umgebung

    Args:
        AppName (str): Name of application
        Verbose (int, optional): Detail of logging. Defaults to 0.
        NoDaemon (bool, optional): Is this an terminal-task. Defaults to True.
        StdErr (bool, optional): Log to StdErr. Defaults to False.
        LogFile (str, optional): Log to a Log-file. Defaults to ''.
        Quiet (bool, optional): Output only errors. Defaults to False.
        ProcInfo (bool, optional): Show process and thread. Defaults to False.
        LevelType (int, optional): Format of LevelInfo. 0=None, 1=Number, 2=Name, 3=Both. Defaults to 2.
        MultiProc (bool, optional): Show process-names. Defaults to False.
        MultiThread (bool, optional): Show thread-names. Defaults to False.
        StackOnDebug (str, optional): Log-level below or equal a stacktrace is included. Defaults to -1 => Disabled.
        StackDepth (int, optional): Maximum number of stack-lines to display. Defaults to 5.
        NoReset (bool, optional): Do not reset logger on init. Defaults to False.
    """    
    if not NoReset:
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
# Add the 3 additional log-level
    add_logging_level('TRACE', logging.DEBUG -5, 'trace')
    add_logging_level('MSG', logging.WARNING - 1, 'msg')
    add_logging_level('STATUS', logging.ERROR - 1, 'status')
# Add the Filter to implement stack-traces
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
    logging.getLogger().addFilter(AddStackContextFilter(StackDepth, Sd))
    
    if not NoDaemon:  # Ausgabe auf StdErr macht als Daemon keinen Sinn
        StdErr = False

    if Quiet:  # Wenn Quiet angegeben ist macht Verbose keinen Sinn
        Verbose = -1

    if Verbose == 0:  # Default
        LogLevel = logging.STATUS
    elif Verbose == 1:  # Mit Infos
        LogLevel = logging.INFO
    elif Verbose == 2:  # Mit Meldungen
        LogLevel = logging.INFO
    elif Verbose == 3:  # Mit debug infos
        LogLevel = logging.DEBUG
    elif Verbose >= 4:  # Mit itrace infos
        LogLevel = logging.TRACE
    else:  # Quiet
        LogLevel = logging.ERROR
    if LevelType == 1:
        ShowLevel = ' - %(levelno)02d'
    elif LevelType == 2:
        ShowLevel = ' - %(levelname)7s'
    elif LevelType == 3:
        ShowLevel = ' - %(levelno)02d=%(levelname)7s'
    else:
        ShowLevel = ''
    if ProcInfo:
        AddPar = ''
        if MultiProc:
            AddPar += '%(processName)s'
        if MultiThread:
            if AddPar != '':
                AddPar += ':'
            AddPar += '%(threadName)s'
        AddPar += ' %(module)s:%(funcName)s:%(lineno)d'
    else:
        AddPar = ''
    
    if LogFile != '':
        Format = f"%(asctime)s - {AppName}:{AddPar}{ShowLevel} - %(message)s%(stack)s"
        FileLogHand = logging.handlers.TimedRotatingFileHandler(LogFile, when = 'S',interval = 60*60*24, backupCount = 5)
        logging.basicConfig(handlers = [FileLogHand], level = LogLevel, format = Format)
        FileLogHand.doRollover()
    elif StdErr:
        if AddPar != '':
            AddPar += '\t'
        if AddPar == '' and ShowLevel == '':
            Format = f"%(asctime)s %(message)s%(stack)s"
        else:
            Format = f"%(asctime)s {AddPar}{ShowLevel} - %(message)s%(stack)s"
        logging.basicConfig(stream = sys.stderr, level = LogLevel, format = Format)
    else:
        Format = f"{AppName}:{AddPar}{ShowLevel} - %(message)s%(stack)s" 
        SysLogHand = logging.handlers.SysLogHandler(address = '/dev/log')
        logging.basicConfig(handlers = [SysLogHand], level = LogLevel, format = Format)

add_logging_level('TRACE', logging.DEBUG -5, 'trace')
add_logging_level('MSG', logging.WARNING - 1, 'msg')
add_logging_level('STATUS', logging.ERROR - 1, 'status')

error = partial(logging.log, logging.ERROR)
warning = partial(logging.log, logging.WARNING)
info = partial(logging.log, logging.INFO)
msg = partial(logging.log,logging.MSG)
status = partial(logging.log,logging.STATUS)
trace = partial(logging.log,logging.TRACE)
debug = partial(logging.log,logging.DEBUG)
log = partial(logging.log)

if __name__ == '__main__':
    import LogP
    
    
    def abc():
        LogP.error('Error')
        LogP.status('Status')
        LogP.warning('Warning')
        LogP.msg('Msg')
        LogP.info('Info')
        LogP.debug('Debug')
        LogP.trace('Trace')
    
    
    def main():
        MyParam= {}
        MyParam['Verbose'] = 3
        MyParam['StdErr'] = True
        MyParam['NoDaemon'] = True
        MyParam['Quiet'] = False
        MyParam['LogFile'] = ''
        MyParam['ProcInfo'] = True
    
    #    MyParam['LogFile'] = './TheLog.log'
        AppName = "LogP"
    
    
        LogP.SetupLogging(AppName, 
            Verbose = MyParam['Verbose'], 
            StdErr = MyParam['StdErr'], 
            NoDaemon = MyParam['NoDaemon'], 
            Quiet = MyParam['Quiet'],
            LogFile = MyParam['LogFile'],
            ProcInfo = False,
            StackOnDebug = "Warning",
            LevelType = 0,
            MultiProc = False, 
            MultiThread = False
            ) 
    
        LogP.error('Error')
        LogP.warning('Warning')
        LogP.info('Info')
        LogP.msg('Msg')
        LogP.status('Status')
        LogP.trace('Trace')
        LogP.debug('Debug')
        abc()
    
        LogP.SetupLogging(AppName, 
            Verbose = MyParam['Verbose'], 
            StdErr = MyParam['StdErr'], 
            NoDaemon = MyParam['NoDaemon'], 
            Quiet = MyParam['Quiet'],
            LogFile = MyParam['LogFile'],
            ProcInfo = True,
            MultiProc = True, 
            MultiThread = True
            ) 
    
        LogP.error('Error')
        LogP.warning('Warning')
        LogP.info('Info')
        LogP.msg('Msg')
        LogP.status('Status')
        LogP.trace('Trace')
        LogP.debug('Debug')
        abc()
    
    
    main()
