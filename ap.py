# On the case that this python library is used, credit must be given to STU940652. 
# Free for non-commercial use.

#   Notes:
# Hasn't been tested on Mac
# setdisplay() seems to be a bit buggy

import os
from sys import platform

displayX = 20
displayY = 20
display = [""]
for i in range(displayY * displayX):
    display.append(" ")

def setdisplay(x, y):
    global displayX, displayY
    displayX = x
    displayY = y
    for i in range(displayY * displayX):
        display.append(" ")

def c():
    if True:
        print ("\n" * 35)
    elif platform == "linux" or platform == "linux2":
        os.system('clear')
    elif platform == "darwin":
        os.system('clear')
    elif platform == "win32":
        os.system('cls')
        
def clear():
    c()
    display = [""]
    for i in range(displayY * displayX):
        display.append(" ")
        
def output(x, y, a):
    x = int(x)
    y = int(y)
    
    pointer = (y * displayX) + x
    b = 0
    
    for i in range(len(a)):
        display[pointer] = a[b]
        b += 1
        pointer += 1
    
def render():
    c()
    for y in range(displayY):
        a = ""
        for x in range(displayX):
            a = a + display[(y * displayY) + x]
        print (a)