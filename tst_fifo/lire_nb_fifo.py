import time
import errno
import os
import random

def safe_read(fd, size=1024):
    ''' reads data from a pipe and returns `None` on EAGAIN '''
    try:
        return os.read(fd, size)
    except OSError, exc:
        if exc.errno == errno.EAGAIN:
            return None
        raise

## Note avec size = 256 => probleme de message tronque
def read_line(fd, size=512):
    data = safe_read(fd, size).split('\n')
    if data:
        for l in data:
            l = l.rstrip()
            yield l

fifo = './fifo'

io = os.open(fifo, os.O_RDONLY | os.O_NONBLOCK)

EXIT = False
while not EXIT:
    for l in read_line(io):
        print "Lecture de [%s] " % l
        n = random.choice([1,2,3])
        print "Attente : %s s" % n
        time.sleep(n) 
        if l == "STOP":
            EXIT = True
    else:
        print "Attente 1s"
        time.sleep(1)
os.close(io)
print "FINI"
