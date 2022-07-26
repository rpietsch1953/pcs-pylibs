#!/usr/bin/env python3
# vim: expandtab:ts=4:sw=4:noai

LogDef = {
    'StdErr': {
        's': 's',
        'l': 'console',
        'm': 'b',
        'v': False,
        'd': """Ausgabe der Statusmeldungen auf die
Konsole und nicht auf syslog""",
        },
    'LogPath': {   
        'l': 'logpath',
        'r': False,
        'o': True,
        'm': 'p',
        'v': '',
        'd': 'Pfad zu einer Log-Datei. Diese wird täglich rotiert und neu erstellt'
        },
    'LogProcInfo': {
        'l': 'logprocinfo',
        'm': 'b',
        'o': True,
        'v': False,
        'd': 'Ausgabe der Procedur und der Zeile',
        },
    'LogProcInfoModLen': {
        'l': 'logmodlen',
        'm': 'i',
        'o': True,
        'v': 15,
        'd': '''Länge der Modulnamen-Ausgabe, 0 = Disabled'''
        },
    'LogProcInfoFuncLen': {
        'l': 'logfunclen',
        'm': 'i',
        'o': True,
        'v': 15,
        'd': '''Länge der Funktionsnamen-Ausgabe, 0 = Disabled'''
        },
    'LogMultiProc': {
        'l': 'logmultiproc',
        'm': 'b',
        'o': True,
        'v': False,
        'd': '''Nur wenn "logprocinfo" gesetzt ist.
zusätzlich Ausgabe des Prozessnamens.
Macht nur bei Programmen mit mehreren Prozessen sinn''',
        },
    'LogMultiProcLen': {
        'l': 'logproclen',
        'm': 'i',
        'o': True,
        'v': 15,
        'd': '''Länge der Procedurnamen-Ausgabe, 0 = Disabled'''
        },
    'LogMultiThread': {
        'l': 'logmultithread',
        'm': 'b',
        'o': True,
        'v': False,
        'd': '''Nur wenn "logprocinfo" gesetzt ist.
zusätzlich Ausgabe des Threadnamens.
Macht nur bei Programmen mit mehreren Threads sinn''',
        },
    'LogMultiThreadLen': {
        'l': 'logthreadlen',
        'm': 'i',
        'o': True,
        'v': 15,
        'd': '''Länge der Threadnamen-Ausgabe, 0 = Disabled'''
        },
    
    'LogLevelType': {
        'l': 'logleveltype',
        'm': 'i',
        'o': True,
        'v': 2,
        'd': '''Ausgabe des Loglevels.
    0 = Keine Ausgabe
    1 = Level-Nummer
    2 = Level-Name
    3 = Beide''',
        },
    'LogStackOnDebug': {
        'l': 'logstack',
        'm': 't',
        'o': True,
        'v': 'NONE',
        'd': '''Ausgabe des Anwendungsstacks ab diesem Level.
Bei verwendung von "LogP" sind die Levels:
    ERROR
    STATUS
    WARNING
    MSG
    INFO
    DEBUG
    TRACE
    NONE
Alle anderen Werte werden als "NONE" interpretiert
Groß- oder Kleinschreibung wird ignoriert''',
        },
    'LogStackDepth': {
        'l': 'logstackdepth',
        'm': 'i',
        'o': True,
        'v': 0,
        'd': '''Anzahl der auszugebenden Stackzeilen, 0 = Disabled'''
        },
    'LogDebugPort': {
        'l': 'logdebugport',
        'm': 'i',
        'o': True,
        'v': 0,
        'd': '''Port auf dem ein debug-server gestartet werden soll, 0 = kein Server'''
        },
    'LogDebugIp': {
        'l': 'logdebugip',
        'm': 't',
        'o': True,
        'v': '127.0.0.1',
        'd': '''Wenn 'logdebugport' aktiviert: die Adresse des Debug-servers.''',
        },
    'LogDebugCacheSize': {
        'l': 'logdebugcache',
        'm': 'i',
        'o': True,
        'v': 0,
        'd': '''Wenn 'logdebugport' aktiviert: Anzahl der 'History'-Ausgabe bei
einer neuer Verbindungs bedeutet es werden die letzten XXX 
Logmeldungen vor der Verbindung ausgegeben und danach 
fortlaufend alle folgenden Meldungen. 0 = Disabled.'''
        },
    'LogStackOnDebug': {
        'l': 'logstackondebug',
        'm': 't',
        'o': True,
        'v': 'NONE',
        'd': '''Ab diesem Log-Level wird ein Stack-Dump an die Meldung angefügt.
Die möglichen Werte sind:
    "ERROR"
    "STATUS"
    "WARNING"
    "MSG"
    "INFO"
    "DEBUG"
    "TRACE"
    "NONE"
Alle anderen Angaben werden als 'NONE' interpretiert. 
Die ANgabe ignoriert Groß- und Kleinschreivbung''',
        },
    'LogLongLevel': {
        'l': 'loglonglevel',
        'm': 't',
        'o': True,
        'v': 'DEBUG',
        'd': '''Ab diesem Log-Level wird die Langform 
(mit allen Processdaten und Log-Level) ausgegeben.
Bei ERROR-Meldungen wird IMMER die Langform verwendet.
Die möglichen Werte sind:
    "ERROR"
    "STATUS"
    "WARNING"
    "MSG"
    "INFO"
    "DEBUG"
    "TRACE"
    "NONE"
Alle anderen Angaben werden als 'NONE' interpretiert. 
Die ANgabe ignoriert Groß- und Kleinschreivbung''',
        },
    'LogStackDepth': {
        'l': 'logstackdepth',
        'm': 'i',
        'o': True,
        'v': 5,
        'd': '''Maximale Anzahl der Stack-Einträge die ausgegeben werden.
Wird nur schlagend wenn 'LogStackOnDebug' nicht 'NONE' ist. 0 = Disabled.'''
        },
    }


