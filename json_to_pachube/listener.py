#!/usr/bin/env python

"""
listener.py is an interface program, between an arduino and Pachube. It 
receives JSON-encoded data from the Arduino and uploads it to Pachube.

Note that your API key and pachube feed ID must be in config.ini for this to work!
"""

from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
from twisted.internet.serialport import SerialPort
from twisted.web import server, resource, client
from twisted.python import usage

from ConfigParser import SafeConfigParser
import logging
import sys
import time
import simplejson as json
from simplejson import JSONDecodeError

class THOptions(usage.Options):
    optParameters = [
        ['baudrate', 'b', 9600, 'Serial baudrate'],
        ['config', 'c', 'config.ini', 'Configuration file'],
        ['port', 'p', '/dev/tty.usbserial-A6008hB0', 'Serial port to use'],
        ]
                                    
class Echo(LineReceiver):
    def update_pachube(self, temp, rh, lux):
    	url = 'http://api.pachube.com/v2/feeds/22374.csv'
    	api_key = open('api.txt').read()
    	data_str = '0,%f\n1,%f\n2,%d\n' % (temp, rh, lux)

    	headers = {'X-PachubeApiKey': api_key}
    	headers['Content-Length'] = str(len(data_str))

    	d = client.getPage(url,method='PUT',postdata=data_str,headers=headers)
    	d.addCallback(lambda _: logging.debug('Pachube updated ok'))
    	d.addErrback(lambda _: logging.error('Error posting to pachube'))

    def processData(self, data):

        lastTemp = data['temp']
        lastRH = data['RH']
        lastLux = data['lux']
        
        logging.info('Sensor: %s Temp: %3.2fC Relative humidity: %3.2f%% Lux: %d' 
            % (data['name'], lastTemp, lastRH, lastLux))

        lastTimestamp = time.time()
	    self.update_pachube(lastTemp, lastRH, lastLux)

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
    logging.basicConfig(level=logging.INFO, \
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
    config_file = o.opts['config']

    logging.debug('About to open port %s' % port)
    s = SerialPort(Echo(), port, reactor, baudrate=baudrate)

    reactor.run()
