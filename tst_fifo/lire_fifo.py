
while True:
    fifo = open("./fifo", "rw")
    for l in fifo:
        print "l=%s " % l
    fifo.close()
