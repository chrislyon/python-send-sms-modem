#! /usr/bin/python
# -*- coding: utf-8 -*-

## ---------------------------
## Serveur d'envoi de SMS
## avec utilisation d'un fifo
## ---------------------------

## Principe simple
## On crée un fifo
## On lance une boucle infini
## qui est chargé de lire une ligne
## et d'envoyer le fifo sur le modem

import os, sys
from stat import *
#import serial
import time
import datetime

import logging

FORMAT = '%(asctime)-15s send_smsd %(message)s'
FIC_LOG = '/var/log/send_smsd.log'
logging.basicConfig(format=FORMAT,filename=FIC_LOG,level=logging.DEBUG)

fifo = '/var/run/send_smsd/send_smsd.fifo'
fifo = './fifo'

STDOUT = True

def log(msg):
    if not STDOUT:
        logging.warning("no=[%s] msg=[%s]" % (no, msg) )
    else:
        ts=datetime.datetime.now()
        print "%s : %s" % (ts.strftime('%j %X'), msg)

## -----------------------------
## Envoi d'un sms sur le modem
## -----------------------------
def send_sms(no, msg):
    log("no=[%s] msg=[%s]" % (no, msg) )
    time.sleep(1)
### Voici la suite pour envoyer sur le modem
#    ser = serial.Serial(
#        port='/dev/ttyACM0',
#        baudrate=115200,
#        parity=serial.PARITY_NONE,
#        stopbits=serial.STOPBITS_ONE,
#        bytesize=serial.EIGHTBITS
#    )
#    ser.open()
#    ser.isOpen()
#    ## Envoi de AT+CMGF=1
#    ser.write("AT+CMGF=1\r\n")
#    time.sleep(1)
#    out=''
#    while ser.inWaiting() > 0:
#        out += ser.read()
#    #print "out=%s" % out
#    ## Envoi de AT+CMGS
#    ser.write("AT+CMGS=%s\r\n" % no)
#    time.sleep(1)
#    out=''
#    while ser.inWaiting() > 0:
#        out += ser.read()
#    #print "out=%s" % out
#    ## Envoi du message + CTRLZ
#    ser.write("%s %s" % (msg, chr(26)))
#    time.sleep(1)
#    out=''
#    while ser.inWaiting() > 0:
#        out += ser.read()
#    #print "out=%s" % out
#    ser.close()

## ----------------------------------------------
## Si le fichier n'existe pas
## on le cree
## Si il existe on verifie si c'est bien du fifo
## ----------------------------------------------
def init_server(fifo):
    log(" Init Server")
    if not os.path.exists(fifo):
        os.mkfifo(fifo)
    else:
        mode = mode = os.stat(fifo).st_mode
        if not S_ISFIFO(mode):
            log( " Type de fichier incorrect %s " % fifo )
            print >> sys.stderr, "Type de fichier incorrect"
            sys.exit(1)

## ------------------
## La boucle infini
## ------------------
##
## Quelques infos :
## ne pas utilliser la formule "with"
## ex: with open(fifo) as io ...
## car dans ce cas la gestion multi process ne se fait pas
## chaque process qui se termine envoi un EOF ce qui peut
## tronquer ce qui est dans le tube
## d'ou l'emploit de la boucle for avec un open mode rw
## et une boucle qui ne s'arrete que si on lui demande
##
def loop(fifo):
    EXIT=False
    while not EXIT:
        log(" Entering loop ")
        log("Open Fifo")
        io = open(fifo, "rw")
        for l in io:
            l = l.rstrip()
            log( "recv : [%s] " % l )
            if l in ('STOP', 'SHUTDOWN'):
                EXIT=True
            all = l.split(':')
            no = all.pop(0)
            msg = ''.join(all)
            if no and msg:
                log("Sending %s %s " % (no, msg))
                send_sms(no, msg)
        log("Closing File")
        io.close()
        time.sleep(3)
        ## On repart :)

    if EXIT:
        log( "Arret de sens_smsd" )

## -------------
## Demarrage
## -------------
def run():
    log( "Lancement de sens_smsd" )
    init_server(fifo)
    loop(fifo)

if __name__ == "__main__":
    run()
