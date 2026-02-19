# -*- coding: utf-8 -*-
"""
Created on Fri Feb 19 16:07:01 2021

@author: Net
$index 1
$list
$comment for a given text file, calculate the character distribution, average and total Entropy
"""

import os
import time
import math

# Pfad relativ zum Skript-Verzeichnis, damit das Skript von überall (z. B. App-Launcher) funktioniert
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(_SCRIPT_DIR, "sampletext.txt")


print('Analyze the file: ',path)
print('\n-----File Contents:---------------------------------------------------')


# open the text file and create a dictionary for the characters 
tokens = dict()
count = 0
try:
    with open(path,'r') as f:
        for line in f:
            print(line)
            for c in line:
                count+=1
                if c in tokens:
                    tokens[c]+=1
                else:
                    tokens[c]=1
except:
    print("File open failed...")
    print('-----End of File---------------------------------------------------\n')

print('Number of characters:',count)
print('Character Dictionary:',tokens)

#convert dictionary into list, and sort the list according to the character count
token_list = sorted(tokens.items(), key = lambda x: x[1],reverse=True)

#compute average entropy per character and total entropy for whole text
print('\n-------Table of characters:----------------')
H_average = 0
for item in token_list:
    p = item[1]/count
    H = math.log(1/p,2)
    p_H = p*H
    if item[0] < ' ':
        print(' {} | cnt={:3d}    p={:1.3f}   H={:3.3f} bit/char  H_av={:3.3f} bit/char'.format(item[0].encode(),item[1],p,H,p_H))
    else:
        print(' {:5} | cnt={:3d}    p={:1.3f}   H={:3.3f} bit/char  H_av={:3.3f} bit/char'.format(item[0],item[1],p,H,p_H))
    H_average += p_H

print('-------------------------------------------\n')
print('Average Entropy H = {:3.3f} bit/char'.format(H_average)   ) 
print('Total Entropy of {:d} characters H={:3.3f} bit'.format(count, H_average*count))  

#infinite loop to keep console open
while True:
    time.sleep(1)
    


