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
import time
import datetime
from ConfigParser import SafeConfigParser

import logging
import pdb

## En exploitation
CONF_FILE = "/etc/send_smsd.conf"
## EN test
#CONF_FILE = "./send_smsd.conf"

## Nombre maximum d'essai
MAX_TRY = 5

## Variable de status de retour 
SMS_OK = True
SMS_KO = False

## -------------------
## ENHANCED SERIAL
## -------------------

"""Enhanced Serial Port class
part of pyserial (http://pyserial.sf.net)  (C)2002 cliechti@gmx.net

another implementation of the readline and readlines method.
this one should be more efficient because a bunch of characters are read
on each access, but the drawback is that a timeout must be specified to
make it work (enforced by the class __init__).

this class could be enhanced with a read_until() method and more
like found in the telnetlib.
"""

from serial import Serial

class EnhancedSerial(Serial):
    def __init__(self, *args, **kwargs):
        #ensure that a reasonable timeout is set
        timeout = kwargs.get('timeout',0.1)
        if timeout < 0.01: timeout = 0.1
        kwargs['timeout'] = timeout
        Serial.__init__(self, *args, **kwargs)
        self.buf = ''
        
    def readline(self, maxsize=None, timeout=1):
        """maxsize is ignored, timeout in seconds is the max time that is way for a complete line"""
        tries = 0
        while 1:
            self.buf += self.read(512)
            pos = self.buf.find('\n')
            if pos >= 0:
                line, self.buf = self.buf[:pos+1], self.buf[pos+1:]
                return line
            tries += 1
            if tries * self.timeout > timeout:
                break
        line, self.buf = self.buf, ''
        return line

    def readlines(self, sizehint=None, timeout=1):
        """read all lines that are available. abort after timout
        when no more data arrives."""
        lines = []
        while 1:
            line = self.readline(timeout=timeout)
            if line:
                lines.append(line)
            if not line or line[-1:] != '\n':
                break
        return lines

## --------
## MODEM
## --------
## On surclasse la classe deja surclasse
## vive l'objet :)
class Modem(EnhancedSerial):
    ## On se simplifie la vie
    def write(self, texte):
        #print "Modem >> %s " % texte
        texte += '\r\n'
        super(Modem, self).write(texte)

    ##On enleve les \r\n inutiles
    def readlines(self, timeout):
        r = super(Modem, self).readlines(timeout)
        r = [ l.rstrip() for l in r ]
        return r


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
    ## Variable de retour
    STATUS_SMS = SMS_KO
    MESSAGE = "ERREUR : Message non initialise"

    ## Ouverture du port
    port = '/dev/ttyACM0'
    try:
        ser = Modem(port)
    except:
        return SMS_KO,  "Probleme ouverture port : %s " % port

    ## Synchronisation
    log( "Synchro Modem" )
    n = 0
    while True:
        ser.write('AT')
        r = ser.readlines(1)
        log( "   r = %s " % r )
        n += 1
        if r[1] == 'OK' or n > 5:
            break
    ##
    ser.write('ATI')
    r = ser.readlines(1)
    log( "   r = %s " % r )
    ## Note la premiere ligne est l'echo de la commande
    OK  = r[1] == 'Cinterion'
    OK *= r[2] == 'EGS3'
    OK *= r[3][0:8] == 'REVISION'
    OK *= r[5] == 'OK'
    if OK:
        log( "Synchro OK" )
    else:
        return SMS_KO, "Probleme synchro MODEM : %s " % r

    ## Envoi de AT+CMGF=1 (passage en mode texte)
    log("Passage en mode texte" )
    ser.write('AT+CMGF=1')
    r = ser.readlines(1)
    log( "   r = %s " % r )
    OK  = r[1] == 'OK'
    if OK:
        log("Mode texte OK")
    else:
        return SMS_KO, "Probleme MODEM passage en mode Texte"

    ## Envoi de AT+CMGS=No_Tel
    log( "Envoi de No de TEL" )
    ser.write('AT+CMGS=%s' % no)
    ## Ici il faut attendre '>'
    r = ser.readlines(1)
    log( "    r = %s " % r )
    OK  = r[1] == '>'
    if OK:
        log( "TEL Ok envoi du msg" )
        ser.write('%s %s' % (msg, chr(26)))
        ## Lecture de l'echo du texte
        r = ser.readlines(1)
        log( "    r = %s " % r )
        ## Attente 
        time.sleep(2)
        ## Lecture du status
        ## OK => r[3]
        ## ERROR => r[1]
        r = ser.readlines(1)
        if len(r) < 1:
            ## ON attend un peu et on recommence
            time.sleep(2)
            r = ser.readlines(1)
            if len(r) < 1:
                ## ON attend un peu et on recommence
                time.sleep(2)
                r = ser.readlines(1)
                if len(r) < 1:
                    return SMS_KO, "PAS DE STATUS ENVOI"
        ## on continue
        log( "    r = %s " % r )
        ERROR = r[1] == 'ERROR'
        if len(r) >= 3:
            OK = r[3] == 'OK'
        else:
            OK = False
        if OK:
            log( "Message bien envoye" )
            STATUS_SMS = SMS_OK
            MESSAGE = "Message envoye"
        elif ERROR:
            return SMS_KO, "ERREUR sur envoi du message %s " % r
        else:
            return SMS_KO, "ERREUR : mauvais status pb modem ? %s " % r
    else:
        return SMS_KO, "Probleme envoi NO TEL"
    log( "Fermeture Modem" )
    ser.close()
    return STATUS_SMS, MESSAGE

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
        ## Trop verbeux
        #log("Entering for loop")
        for l in read_line(io):
            if l:
                log( "recv : [%s] " % l )
            if l in ('STOP', 'SHUTDOWN'):
                log('receive stop')
                EXIT=True

            all = l.split(':')
            no = all.pop(0)
            msg = ''.join(all)
            if no and msg:
                log("Sending sms")
                ST, MSG = send_sms(no, msg)
                if ST:
                    log("sms sended")
                else:
                    n = NB_TRY.get(no, 0)
                    NB_TRY[no] = n+1
                    EN_ATTENTE.append( (no, msg) )
                    log("sms not sended no=%s NB_TRY=%s MSG=%s" % (no, NB_TRY[no], MSG))

        else:
            ## Trop verbeux
            #log("En attente ? %s " % len(EN_ATTENTE))
            while len(EN_ATTENTE):
                sms = EN_ATTENTE.pop(0)
                log("after pop : En attente ? %s " % len(EN_ATTENTE))
                no = sms[0]
                msg = sms[1]
                if NB_TRY[no] < MAX_TRY:
                    ST, MSG = send_sms(no, msg)
                    if ST:
                        log("sms %s sended after %s tries" % (no, NB_TRY[no]))
                    else:
                        ## on remet dans la boucle
                        EN_ATTENTE.append( (no, msg) )
                        ## On incremente le compteur
                        n = NB_TRY.get(no, 0)
                        NB_TRY[no] = n+1
                        log("sms not sended no=%s NB_TRY=%s MSG=%s" % (no, NB_TRY[no], MSG))
                else:
                    log("Abandon pour %s apres %s essais" % (no, NB_TRY[no]))
                    ## c'est deja retirer de EN_ATTENTE
                    ## reste NB_TRY
                    del NB_TRY[no]
        ## Trop verbeux
        #log("Attente")
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
