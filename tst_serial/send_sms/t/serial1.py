import time
import serial

# configure the serial connections (the parameters differs on the device you are connecting to)
ser = serial.Serial(
    port='/dev/ttyACM0',
    baudrate=115200,
    timeout=1,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS
)

ser.open()
ser.isOpen()

print 'Enter your commands below.\r\nInsert "exit" to leave the application.'

input=1
while 1 :
    # get keyboard input
    input = raw_input(">> ")
        # Python 3 users
        # input = input(">> ")
    if input == 'exit':
        ser.close()
        exit()
    else:
        # send the character to the device
        # (note that I happend a \r\n carriage return and line feed to the characters - this is requested by my device)
        ser.write(input + '\r\n')
        out = ''
        ## let's wait one second before reading output (let's give device time to answer)
        time.sleep(1)
        while ser.inWaiting() > 0:
            c = ser.read(1)
            if c == '\r':
                continue
            if c == '\n':
                break
            out += c

        print ">>[%s]" % out
        for c in out:
            print "%02d " % ord(c),
        print
