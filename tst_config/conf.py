
from ConfigParser import SafeConfigParser

parser = SafeConfigParser()
parser.read('example.conf')

print "MAIN:log_path", parser.get('MAIN', 'log_path')
print "MAIN:fifo_path", parser.get('MAIN', 'fifo_path')
