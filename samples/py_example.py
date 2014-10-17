#!/usr/bin/python -tt
# vim: set ts=4 sw=4 tw=79 et :

import time
import gryphie as g

#setup a cfg dict we can pass to the back-ends
cfg = { 'librato_email' : 'dave@someplace.org',
        'librato_token' : '12345678abcdefghij',
        'librato_whitelist' : ["load", "swap"],
        'carbon_servers' : '127.0.0.1:2003',
        'statsd_servers' : '127.0.0.1:8125',
       }

senders =  [ g.librato(cfg),
             g.carbon(cfg),
             g.statsd(cfg),
             g.stdout(cfg),
           ]

datapoints=[]
datapoint = g.Measurement()
datapoint.NAME = 'DC1.Webservers.HOST23.cpu.load.load5'
datapoint.SOURCE = 'HOST23'
datapoint.VALUE = '.2'
datapoint.TIME = str(time.time())

datapoints.append(datapoint)

for sender in senders:
    sender.send(datapoints)
