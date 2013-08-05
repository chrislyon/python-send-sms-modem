#! /usr/bin/env python
# -*- coding: utf-8 -*-

## --------------------------
## Envoi d'un sms en python
## --------------------------

import sys
import time
import serial

def usage(prog_name):
	print "Usage %s : numero message" % prog_name
	print "numero = numero de telephone"
	print "message = le message transmettre avec guillemet si espace"
	sys.exit(1)

def send_sms(no, msg):
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
	print "out=%s" % out
	## Envoi de AT+CMGS
	ser.write("AT+CMGS=%s\r\n" % no)
	time.sleep(1)
	out=''
	while ser.inWaiting() > 0:
		out += ser.read()
	print "out=%s" % out
	## Envoi du message + CTRLZ
	ser.write("%s %s" % (msg, chr(26)))
	time.sleep(1)
	out=''
	while ser.inWaiting() > 0:
		out += ser.read()
	print "out=%s" % out
	ser.close()
	exit()

if __name__ == '__main__':
	if len(sys.argv) < 2:
		usage(sys.argv[0])
	else:
		send_sms(sys.argv[1], sys.argv[2])
