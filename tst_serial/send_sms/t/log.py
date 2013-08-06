import logging

FORMAT = '%(asctime)-15s send_smsd %(message)s'
logging.basicConfig(format=FORMAT,filename='example.log',level=logging.DEBUG)
logging.info("MESSAGE")
logging.warning("SANS NO")
logging.warning("no=%s msg=%s" % ('0606060606', 'Message_sms'))
