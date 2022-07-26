#!/usr/bin/env python3
# vim: expandtab:ts=4:sw=4:noai

from Log_Args import LogDef
GlobalDef = {
    'Help': {
        's': 'h',
        'l': 'help',
        'm': 'H',
        'd': 'Diesen Hilfetext anzeigen und beenden'
        },
    'Verbose': {
        's': 'v',
        'l': 'verbose',
        'r': False,
        'm': 'C',
        'd': """Ausgabe von Statusmeldungen
für mehr Details die kurze Option mehrmals angeben oder
die lange Option mit einer höheren Zahl verwenden.""",
        },
    'Quiet': {
        's': 'q',
        'l': 'quiet',
        'm': 'b',
        'd': 'Nur Fehler ausgeben'
        },
    'Export': {
        's': 'x',
        'l': 'export',
        'm': 'X',
        'd': 'Ausgabe der aktuellen Konfiguration und Beenden'
        },
    'ConfFile': {
        's': 'c',
        'l': 'config',
        'm': 'x',
        'd': '''Zuerst die Werte aus der Datei lesen,
        danach erst die Komandozeilenparameter'''
        },
    'GlobalExport': {
        'l': 'globexport',
        'm': '>',
        'd': 'Ausgabe aller Konfigurationen und Beenden'
        },
    'GlobImport': {
        's': 'g',
        'l': 'globconfig',
        'm': '<',
        'o': True,
        'd': '''Globale Config. Zuerst die Werte aus der Datei lesen,
danach erst die Komandozeilenparameter'''
        },
    'NoDaemon': {
        's': 'd',
        'l': 'nodaemon',
        'm': 'b',
        'v': False,
        'd': 'Start im Vordergrund (Nicht als Daemon) für Test',
        },
    }

TestDef_Alpha =     {
    'Count': {
        's': 'C',
        'l': ('count','Count'),
        'r': True,
        'o': True,
        # 'v': 7,
        'm': 'i',
        'L': 1,
        'U': 10,
        'd': 'Eine Zahl zwischen 1 und 10',
        },
    'Text': {
        's': 't',
        'l': ('text','Text'),
        'o': True,
        'L': 'a',
        'U': 'zAA',
        'v': '',
        'm': 't',
        'd': 'Ein Text',
        },
    }

TestDef_Beta =     {
#    'Help': {
#        's': 'h',
#        'l': 'help',
#        'm': 'H',
#        'd': 'Diesen Hilfetext anzeigen und beenden'
#        },
    }

TestDef_Gamma =     {
    'Xy': {
        's': 'b',
        'l': 'bbbb',
        'o': True,
        'm': 'b',
        'd': 'Ein Switch'
        },
    }

Children = {
    'Log':
        {
        'Desc': "Logging Optionen",
        'Def': LogDef,
        },
    'Alpha':
        {
        'Desc': "Description Alpha",
        'Def': TestDef_Alpha,
        'Children': {
            'Gamma': {
                'Desc': "Description Gammy",
                'Def': TestDef_Gamma,
                }
            }
        },
    'Beta':
        {
        'Def': TestDef_Beta,
        'Desc': "Description Beta",
        'Children': {}
        }
    }
