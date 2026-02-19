
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 19 16:07:01 2021

@author: Net
$list
$comment create a dictionary for words in a text file
$index 1
"""

import os,time,math

cwd=os.getcwd()
print('Current Working Directory=',cwd)
pos = cwd.find('topics')
#print('pos',pos)
if pos == -1:
    path = os.path.join('topics','01_DataCompression','sidedata','sampletext.txt')
else:
    path = os.path.join(cwd[:pos],'topics','01_DataCompression','sidedata','sampletext.txt')
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
print('Total Entropy of {:d} words H={:3.3f} bit ({} bytes)'.format(count, H_average*count,int(H_average*count/8)))  
print('Size of text file: {} bytes'.format(os.path.getsize(path)))

#infinite loop to keep console open
while True:
    time.sleep(1)
    


