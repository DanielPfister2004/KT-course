# -*- coding: utf-8 -*-
"""
Created on Fri Feb 19 16:07:01 2021

@author: Net
$list
$comment create a dictionary for words in a text file
$index 1
"""

import os
import sys
import time
import math

# Pfad relativ zum Skript-Verzeichnis, damit das Skript von überall (z. B. App-Launcher) funktioniert
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(_SCRIPT_DIR, "sampletext.txt")

# Konsolenausgabe parallel in submissions/console_log.txt schreiben (für Launcher „Konsolenausgabe einfügen“)
_CONSOLE_LOG_PATH = os.path.join(_SCRIPT_DIR, "submissions", "console_log.txt")


class _Tee:
    """Schreibt gleichzeitig in mehrere Streams (z. B. Konsole + Datei)."""
    def __init__(self, *streams):
        self.streams = streams
    def write(self, data):
        for s in self.streams:
            s.write(data)
            if getattr(s, "flush", None):
                s.flush()
    def flush(self):
        for s in self.streams:
            if getattr(s, "flush", None):
                s.flush()
    def writable(self):
        return True


_log_file = None
try:
    os.makedirs(os.path.dirname(_CONSOLE_LOG_PATH), exist_ok=True)
    _log_file = open(_CONSOLE_LOG_PATH, "w", encoding="utf-8")
    sys.stdout = _Tee(sys.__stdout__, _log_file)
except OSError:
    pass  # ohne Log-Datei weiterlaufen


print('Analyze the file: ',path)
tokens = dict()
count = 0

# open the text file and create a dictionary for the characters 
with open(path,'r') as f:
    for line in f:
        line = line.replace(',',' ')
        line = line.replace('.',' ')
        words = line.split()
        for word in words:
            count+=1
            if word in tokens:
                tokens[word]+=1
            else:
                tokens[word]=1

print('Total number of words:    ',count)
print('Number of different words:',len(tokens))

#convert dictionary into list, and sort the list according to the character count
token_list = sorted(tokens.items(), key = lambda x: x[1],reverse=True)

#compute average entropy per character and total entropy for whole text
print('\n-------Table of words:-----------------------------------------')
H_average = 0
for item in token_list:
    p = item[1]/count
    H = math.log(1/p,2)
    p_H = p*H
    print(' {:>30} | cnt={:3d}    p={:1.3f}   H={:3.3f} bit/word   H_av={:3.3f} bit/word'.format(item[0],item[1],p,H,p_H))
    H_average += p_H

print('-----------------------------------------------------------------\n')
print('Average Entropy H = {:3.3f} bit/word'.format(H_average)   ) 
print('Total Entropy of {:d} words H={:3.3f} bit ({} bytes)'.format(count, H_average*count, math.ceil(H_average*count/8)))  
print('Size of text file: {} bytes'.format(os.path.getsize(path)))

# Log-Datei schließen, danach Konsole normal weiter nutzen (Endlosschleife)
if _log_file is not None:
    try:
        sys.stdout = sys.__stdout__
        _log_file.close()
    except (OSError, NameError):
        pass

#infinite loop to keep console open
while True:
    time.sleep(1)
    


