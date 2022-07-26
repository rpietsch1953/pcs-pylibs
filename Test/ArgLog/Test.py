#!/usr/bin/env python3
# vim: expandtab:ts=4:sw=4:noai

"""Test pcs-argpass und pcs-log
"""
import logging
import sys
from pcs_log.LogP import LogP
from pcs_argpass.Param import Param, Translation_de_DE
from Test_Args import GlobalDef, Children

MyParam = Param( Def=GlobalDef,Children = Children)
MyParam.SetTranslation(Translation_de_DE)
try:
    Erg = MyParam.Process()
except Param.ParamError as exc:
    print(exc)
    sys.exit(1)
# print(MyParam.ParamStr(indent=2))

ZusArgs = MyParam.GetRemainder()
if len(ZusArgs) > 0:
    print(f"Fehler: Zusätzliche, unerwartete Argumente: {ZusArgs}")
    sys.exit(1)
lp = MyParam.Child['log']

# print(lp.ParamStr(2))

# LogP.SetupLogging(  AppName=MyParam.MyProgName(),
#                     Verbose=lp['Verbose'],
#                     NoDaemon=lp['NoDaemon'],
#                     StdErr=lp['StdErr'],
#                     LogPath=lp['LogPath'],
#                     Quiet=lp['Quiet'],
#                     LogProcInfo=lp['LogProcInfo'],
#                     LogProcInfoModLen=lp['LogProcInfoModLen'],
#                     LogProcInfoFuncLen=lp['LogProcInfoFuncLen'],
#                     LogLevelType=lp['LogLevelType'],
#                     LogMultiProc=lp['LogMultiProc'],
#                     LogMultiProcLen=lp['LogMultiProcLen'],
#                     LogMultiThread=lp['LogMultiThread'],
#                     LogMultiThreadLen=lp['LogMultiThreadLen'],
#                     LogStackOnDebug=lp['LogStackOnDebug'],
#                     LogStackDepth=lp['LogStackDepth'],
#                     LogDebugIp=lp['LogDebugIp'],
#                     LogDebugPort=lp['LogDebugPort'],
#                     LogDebugCacheSize=lp['LogDebugCacheSize']
#                     )

LogP.SetupLogging(  AppName=MyParam.MyProgName(), **MyParam.Child['log'])
#LogServer = LogP.SetupLogging(  AppName=MyParam.MyProgName(), **lp)
Ret = input('Type [ENTER]: ')

logging.status('Start')
for l in MyParam.ParamStr().splitlines():
    logging.msg(l)

logging.error('Error 1')
logging.status('Status 2')
logging.warning('Warning 3')
logging.msg('Msg 4')
logging.info('Info 5')
logging.debug('Debug 6')
logging.trace('Trace 7')


Ret = input('Type [ENTER]: ')
logging.status('Stop')
LogP.Stop()
#
