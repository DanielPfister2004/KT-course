# -*- coding: utf-8 -*-
"""
Created on Thu Feb 18 18:21:11 2021

@author: 
https://www.programiz.com/dsa/huffman-coding
$list
$comment Enter a string of characters and compute the Huffman code tree
$index 2
"""

import os
import sys
import time

# Konsolenausgabe parallel in submissions/console_log.txt schreiben (für Launcher „Konsolenausgabe einfügen“)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
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

# Huffman Coding in python

#string = 'BCAADDDCCACACAC'
string = input("Enter the string to compute Huffman Code Tree: ")
print('---------------------------------------------------------')


# Creating tree nodes
class NodeTree(object):

    def __init__(self, left=None, right=None):
        self.left = left
        self.right = right

    def children(self):
        return (self.left, self.right)

    def nodes(self):
        return (self.left, self.right)

    def __str__(self):
        return '%s_%s' % (self.left, self.right)


# Main function implementing huffman coding
def huffman_code_tree(node, left=True, binString=''):
    if type(node) is str:
        return {node: binString}
    (l, r) = node.children()
    d = dict()
    d.update(huffman_code_tree(l, True,  binString + '0'))
    d.update(huffman_code_tree(r, False, binString + '1'))
    return d


# Calculating frequency of chars
freq = {}
for c in string:
    if c in freq:
        freq[c] += 1
    else:
        freq[c] = 1

print('Dictionary of Characters with char frequency:      ',freq)
print('Dictionary converted into a list:                  ',freq.items())
#The sorted() function returns a sorted list of the specified iterable object.
freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)
print('List of characters sorted to descending frequency: ',freq)
nodes = freq

while len(nodes) > 1:
    (key1, c1) = nodes[-1]
    (key2, c2) = nodes[-2]
    nodes = nodes[:-2]
    node = NodeTree(key1, key2)
    nodes.append((node, c1 + c2))
    nodes = sorted(nodes, key=lambda x: x[1], reverse=True)

huffmanCode = huffman_code_tree(nodes[0][0])
print('Huffman Code Dictionary:                           ',huffmanCode)

print('\n Char | Huffman code ')
print('----------------------')
for (char, frequency) in freq:
    print(' %-4r |%12s' % (char, huffmanCode[char]))

# Log-Datei schließen, danach Konsole normal weiter nutzen (Endlosschleife)
if _log_file is not None:
    try:
        sys.stdout = sys.__stdout__
        _log_file.close()
    except (OSError, NameError):
        pass

while True:
    time.sleep(1)    