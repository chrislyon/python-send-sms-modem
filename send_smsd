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
import serial
import time


import logging

FORMAT = '%(asctime)-15s send_smsd %(message)s'
FIC_LOG = '/var/log/send_smsd.log'
logging.basicConfig(format=FORMAT,filename=FIC_LOG,level=logging.DEBUG)

## -----------------------------
## Envoi d'un sms sur le modem
## -----------------------------
def send_sms(no, msg):
    logging.warning("no=[%s] msg=[%s]" % (no, msg) )
    ser = serial.Serial(
        port='/dev/ttyACM0',
        baudrate=115200,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS
    )
    ser.open()
    ser.isOpen()
    ## Envoi de AT+CMGF=1
    ser.write("AT+CMGF=1\r\n")
    time.sleep(1)
    out=''
    while ser.inWaiting() > 0:
        out += ser.read()
    #print "out=%s" % out
    ## Envoi de AT+CMGS
    ser.write("AT+CMGS=%s\r\n" % no)
    time.sleep(1)
    out=''
    while ser.inWaiting() > 0:
        out += ser.read()
    #print "out=%s" % out
    ## Envoi du message + CTRLZ
    ser.write("%s %s" % (msg, chr(26)))
    time.sleep(1)
    out=''
    while ser.inWaiting() > 0:
        out += ser.read()
    #print "out=%s" % out
    ser.close()

## ----------------------------------------------
## Si le fichier n'existe pas
## on le cree
## Si il existe on verifie si c'est bien du fifo
## ----------------------------------------------
def init_server(fifo):
    logging.warning(" Init Server")
    if not os.path.exists(fifo):
        os.mkfifo(fifo)
    else:
        mode = mode = os.stat(fifo).st_mode
        if not S_ISFIFO(mode):
            logging.warning( " Type de fichier incorrect %s " % fifo )
            print >> sys.stderr, "Type de fichier incorrect"
            sys.exit(1)

## ------------------
## La boucle infini
## ------------------
def loop(fifo):
    EXIT=False
    while not EXIT:
        logging.warning(" Entering loop ")
        with open(fifo) as io:
            buffer = io.read(2048)
            for l in buffer.split('\n'):
                if l:
                    logging.info( "recv : [%s] " % l )
                    if l in ('STOP', 'SHUTDOWN'):
                        EXIT=True
                    all = l.split(':')
                    no = all.pop(0)
                    msg = ''.join(all)
                    if no and msg:
                        send_sms(no, msg)
    if EXIT:
        logging.warning( "Arret de sens_smsd" )

## -------------
## Demarrage
## -------------
def run():
    logging.warning( "Lancement de sens_smsd" )
    fifo = '/var/run/send_smsd/send_smsd.fifo'
    init_server(fifo)
    loop(fifo)

if __name__ == "__main__":
    run()
