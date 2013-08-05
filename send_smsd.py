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

import os, sys, traceback
import errno
from stat import *
#import serial
import time
import datetime
from ConfigParser import SafeConfigParser
import random

import logging
import pdb

RANDOM = [True, False, False]


## En exploitation
CONF_FILE = "/etc/send_smsd.conf"
## EN test
CONF_FILE = "./send_smsd.conf"

## Nombre maximum d'essai
MAX_TRY = 5

## -------------------
## Sortie sur erreur
## -------------------
def sortie(msg):
    log("ERROR: %s " % msg)
    print >> sys.stderr, '-'*60
    traceback.print_exc(file=sys.stderr)
    print >> sys.stderr, '-'*60
    print >> sys.stderr,  "ERR: %s" % msg
    sys.exit(1)

def log(msg):
    logging.warning(msg)
    #ts=datetime.datetime.now()
    #print "%s : %s" % (ts.strftime('%j %X'), msg)

## -----------------------------
## Envoi d'un sms sur le modem
## -----------------------------
def send_sms(no, msg):
    log("no=[%s] msg=[%s]" % (no, msg) )
    time.sleep(1)
    ## Pour l'instant rien ne fonctionne :)
    return random.choice( RANDOM )
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
    log("Init Server verif fifo")
    if not os.path.exists(fifo):
        os.mkfifo(fifo)
    else:
        mode = mode = os.stat(fifo).st_mode
        if not S_ISFIFO(mode):
            sortie("Type de fichier incorrect")


## -------------------------------
## Lecture non bloquante du fifo
## Trouve sur 
## http://stackoverflow.com/questions/14345816/how-python-read-named-fifo-non-blockingly?rq=1
## -------------------------------
def safe_read(fd, size=1024):
    ''' reads data from a pipe and returns `None` on EAGAIN '''
    try:
        return os.read(fd, size)
    except OSError, exc:
        if exc.errno == errno.EAGAIN:
            return None
        raise

## ----------------------------------------------------
## Ca c'est presque que moi mais bon
## apres lecture d'une foultitude d'exemple sur le net
## ----------------------------------------------------
def read_line(fd, size=256):
    for l in safe_read(fd, size).split('\n'):
        l = l.rstrip()
        yield l

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
    EN_ATTENTE = []
    NB_TRY = {}
    log("Open Fifo")
    io = os.open(fifo, os.O_RDONLY | os.O_NONBLOCK)
    while not EXIT:
        log("Entering for loop")
        for l in read_line(io):
            log( "recv : [%s] " % l )
            if l in ('STOP', 'SHUTDOWN'):
                log('receive stop')
                EXIT=True

            all = l.split(':')
            no = all.pop(0)
            msg = ''.join(all)
            if no and msg:
                log("Sending sms")
                if send_sms(no, msg):
                    log("sms sended")
                else:
                    n = NB_TRY.get(no, 0)
                    NB_TRY[no] = n+1
                    EN_ATTENTE.append( (no, msg) )
                    log("sms not sended no=%s NB_TRY=%s" % (no, NB_TRY[no]))

        else:
            log("En attente ? %s " % len(EN_ATTENTE))
            while len(EN_ATTENTE):
                sms = EN_ATTENTE.pop(0)
                log("after pop : En attente ? %s " % len(EN_ATTENTE))
                no = sms[0]
                msg = sms[1]
                if NB_TRY[no] < MAX_TRY:
                    if send_sms(no, msg):
                        log("sms %s sended after %s tries" % (no, NB_TRY[no]))
                    else:
                        ## on remet dans la boucle
                        EN_ATTENTE.append( (no, msg) )
                        ## On incremente le compteur
                        n = NB_TRY.get(no, 0)
                        NB_TRY[no] = n+1
                        log("sms not sended no=%s NB_TRY=%s" % (no, NB_TRY[no]))
                else:
                    log("Abandon pour %s apres %s essais" % (no, NB_TRY[no]))
                    ## c'est deja retirer de EN_ATTENTE
                    ## reste NB_TRY
                    del NB_TRY[no]
        log("Attente")
        time.sleep(3)
        ## J'ai tout lu mais ais je bien bien tout envoye
        ## On repart :)
    if EXIT:
        log( "Arret de boucle principale" )
    log("Closing File")
    os.close(io)

## -----------------
## Recupere la conf
## -----------------
def get_conf( conf_file ):
    global fifo
    ## Verif du fichier de conf
    try:
        parser = SafeConfigParser()
        parser.read(conf_file)
    except:
        sortie("Erreur fichier de conf : %s " % conf_file )
    ## Verif des principales variables
    try:
        fifo = parser.get('MAIN', 'fifo_path')
    except:
        sortie("Probleme configuration fifo_path")

    ## Fichier de log
    try:
        FORMAT = '%(asctime)-15s send_smsd %(message)s'
        FIC_LOG = parser.get('MAIN', 'log_path')
        logging.basicConfig(format=FORMAT,filename=FIC_LOG,level=logging.DEBUG)
    except:
        sortie("Probleme fichier de log")


## -------------
## Demarrage
## -------------
def run():
    get_conf( CONF_FILE )
    log( "Lancement de sens_smsd" )
    log( "Fichier de conf : %s " % CONF_FILE )
    init_server(fifo)
    loop(fifo)
    log("Fin de send_smsd")

if __name__ == "__main__":
    #pdb.set_trace()
    run()
