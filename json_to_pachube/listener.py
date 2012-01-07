#!/usr/bin/env python

# pfh 6/15/09
# Starting from http://itamarst.org/writings/etech04/twisted_internet-22.html
# Goal: Listen to arduino, save data in engineering units, to CSV, also present
# in twisted.web or similar. Socket server?
#
# Serial code from http://twistedmatrix.com/projects/core/documentation/examples/gpsfix.py

from twisted.protocols.basic import LineReceiver

from twisted.internet import reactor
from twisted.internet.serialport import SerialPort
from twisted.web import server, resource, client

from twisted.python import usage
import logging
import sys
import time
import simplejson as json
from simplejson import JSONDecodeError

lastTemp = 0.0
lastRH = 0.0
lastLux = 0
lastTimestamp = 0

class THOptions(usage.Options):
    optParameters = [
        ['baudrate', 'b', 9600, 'Serial baudrate'],
        ['port', 'p', '/dev/tty.usbserial-A6008hB0', 'Serial port to use'],
        ]


class Echo(LineReceiver):
    def processData(self, data):

        global lastTemp, lastRH, lastTimestamp, lastLux

        lastTemp = data['temp']
        lastRH = data['RH']
        lastLux = data['lux']
        lastTimestamp = time.time()
        
        # Update screen now and then
        if (time.time() - lastTimestamp) > 20.0:
            logging.info('Temp: %f C Relative humidity: %f %% Lux: %f' % (lastTemp, lastRH, lastLux))

    def connectionMade(self):
        logging.info('Serial connection made!')

    def lineReceived(self, line):
        logging.debug('Line: "%s"' % line);

        try:
            data = json.loads(line);
        except JSONDecodeError, jde:
            logging.exception(jde)
            return

        self.processData(data)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, \
                format='%(asctime)s %(levelname)s [%(funcName)s] %(message)s')

    o = THOptions()
    try:
        o.parseOptions()
    except usage.UsageError, errortext:
        logging.error('%s %s' % (sys.argv[0], errortext))
        logging.info('Try %s --help for usage details' % sys.argv[0])
        raise SystemExit, 1

    if o.opts['baudrate']:
        baudrate = int(o.opts['baudrate'])

    port = o.opts['port']

    logging.debug('About to open port %s' % port)
    s = SerialPort(Echo(), port, reactor, baudrate=baudrate)

    reactor.run()
