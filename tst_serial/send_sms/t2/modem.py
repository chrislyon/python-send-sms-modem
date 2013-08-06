import serial
import traceback
import os, sys

## -------------------
## Sortie sur erreur
## -------------------
def sortie(msg):
    print >> sys.stderr, '-'*60
    traceback.print_exc(file=sys.stderr)
    print >> sys.stderr, '-'*60
    print >> sys.stderr,  "ERR: %s" % msg
    sys.exit(1)


if __name__ == '__main__':
    test()
