#! /usr/bin/env python
# -*- coding: utf-8 -*-

## --------------------------
## Envoi d'un sms en python
## --------------------------

##
## J'ai prefere tout mettre dans un seul fichier 
## c'est plus simple a gerer dans mon cas
##

import sys
import time
import traceback
import os, sys

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

SMS_OK = True
SMS_KO = False

## -------------------
## Sortie sur erreur
## -------------------
def sortie(msg):
    print >> sys.stderr, '-'*60
    traceback.print_exc(file=sys.stderr)
    print >> sys.stderr, '-'*60
    print >> sys.stderr,  "ERR: %s" % msg
    sys.exit(1)

def usage(prog_name):
    print "Usage %s : numero message" % prog_name
    print "numero = numero de telephone"
    print "message = le message transmettre avec guillemet si espace"
    sys.exit(1)

def log(msg='<vide>'):
        print "==> %s " % msg

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

if __name__ == '__main__':
    if len(sys.argv) < 2:
        usage(sys.argv[0])
    else:
        S, M = send_sms(sys.argv[1], sys.argv[2])
        print "Status = %s / Msg= %s" % (S, M)
