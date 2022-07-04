#!/usr/bin/env python3
# vim: expandtab:ts=4:sw=4:noai

from Test_Args import GlobalDef, Children
from pcs_argpass.Param import Param
import pcs_log.LogP as LogP

MyParam = Param( Def=GlobalDef,Children = Children)
MyParam.Process()
print(MyParam.ParamStr(indent=2))

lp = MyParam.Child['log']

print(lp.ParamStr(2))

# LogServer = LogP.SetupLogging(  AppName=MyParam.MyProgName(),
#                                Verbose=lp['Verbose'],
#                                NoDaemon=lp['NoDaemon'],
#                                StdErr=lp['StdErr'],
#                                LogPath=lp['LogPath'],
#                                Quiet=lp['Quiet'],
#                                LogProcInfo=lp['LogProcInfo'],
#                                LogProcInfoModLen=lp['LogProcInfoModLen'],
#                                LogProcInfoFuncLen=lp['LogProcInfoFuncLen'],
#                                LogLevelType=lp['LogLevelType'],
#                                LogMultiProc=lp['LogMultiProc'],
#                                LogMultiProcLen=lp['LogMultiProcLen'],
#                                LogMultiThread=lp['LogMultiThread'],
#                                LogMultiThreadLen=lp['LogMultiThreadLen'],
#                                LogStackOnDebug=lp['LogStackOnDebug'],
#                                LogStackDepth=lp['LogStackDepth'],
#                                LogDebugIp=lp['LogDebugIp'],
#                                LogDebugPort=lp['LogDebugPort'],
#                                LogDebugCacheSize=lp['LogDebugCacheSize']
#                                )
LogServer = LogP.SetupLogging(  AppName=MyParam.MyProgName(), **lp)
LogP.status('Start')


LogP.error('Error 1')
LogP.status('Status 2')
LogP.warning('Warning 3')
LogP.msg('Msg 4')
LogP.info('Info 5')
LogP.debug('Debug 6')
LogP.trace('Trace 7')


Ret = input('Type [ENTER]: ')
LogP.status('Stop')
LogServer.Stop()
LogServer.Join(2)
LogServer.Kill()




