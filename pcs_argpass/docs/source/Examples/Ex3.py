#!/usr/bin/env python3
# vim: expandtab:ts=4:sw=4:noai


import sys
from pcs_argpass.Param import Param
from pcs_argpass.GPL3 import GPL3_2007, GPL_Preamble, LGPL3_2007
from Ex3_Args import Def_Main, Child_Def

MyParam:Param = None              # to produce an error if not initialized!
Version = "1.0.0"

def main():

    # do your work here.
    print(MyParam.ParamStr())       # only to do something
    
    AddPar = MyParam.Child['add']   # you can get a sub-part of your definitions
    for key,value in AddPar.items():
        print(f"{key} -> {value}")

if __name__ == '__main__':
    try:                                            # catch illegal definitions
        MyParam = Param(Def=Def_Main,
                        Desc="Manage names",
                        AllParams=True,
                        Children=Child_Def,
                        Version=Version,
                        ShowPrefixOnHelp=False,
#                        translation=Translation_de_DE, # remove this line for english messages
                        License=('\nCopyright (c) 2022 <your name>\n' + GPL_Preamble, GPL3_2007))
        print(MyParam.TestCommandLineParameter)
        if not MyParam.Process():
            main()
    except Param.ParamError as RunExc:      # here we catch any parameter errors and inform the user
        print(f"{RunExc }",file=sys.stderr)
        sys.exit(1)
    sys.exit(0)

