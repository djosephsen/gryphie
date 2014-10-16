Gryphie
=======

#### Graphs in a jiffy!
Gryphie makes it easy to wire that thing you're working on to the various
time-series storage and visualization systems like
[Graphite](http://graphite.readthedocs.org/en/latest/overview.html),
[InfluxDB](http://influxdb.com/), [Librato](http://metrics.librato.com), and
[OpenTSDB](http://opentsdb.org). 

#### Talk to lots of different metrics back-ends at the same time
If you're sick of trying to track multiple language bindings for different
metrics-backends in your codebase, then you'll probably appreciate Gryphie.
With Gryphie, your thing can emit metrics to any combination of these systems
simultaneously. You can measure something, and then easily send your
measurement to two different Graphite systems, an Influx box and Librato.  At
the moment Gryphie only works with python things, but soon it'll work with Go
and Ruby things too. Gryphie makes it pretty easy to expose different back-end
metrics systems to your users without forcing you to implement a binding for
each.

#### Gryphie is pretty easy to wrap your head around
Gryphie implements [carbon](), [statsd](), and [librato
api](http://metrics.librato.com) objects, which use common interface semantics
for things like sending metrics .  The general pattern is, you instantiate an
object for each back-end you want to talk to, passing each a small
configuration struct when you first instantiate it. I like to keep an array of
references to them, so when I'm ready to send a measurement, I can just iterate
across the backend objects, calling the send() method of each in turn. Here's a
small Python program that should give you a good feel for how easy it is to
deal with metrics backends using Gryphie: 

     import time
     import gryphie as g
     
     #setup a cfg dict we can pass to the back-ends
     cfg = { 'librato_email' : 'dave@someplace.org',
             'librato_token' : '12345678abcdefghij',
             'librato_whitelist' : ["load", "swap"],
             'carbon_servers' : '127.0.0.1:2003 192.168.1.2:2003',
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

#### Efficient and pedantic, but never annoying
Gryphie tries to insulate you from wire protocol details, while still
optimizing for transport efficiency by doing things like buffering and
combining individual measurements, and using compression and binary protocols
where possible.  It also tries to do this with a minimum of dependencies.
Gryphie's python implementation, for example, reimplements each protocol on top
of the python standard library, and doesn't use any external dependencies.
Gryphie isn't just a wrapper around other protocol bindings.

#### Gryphie is a work in progress
I unintentionally created gryphie while ripping the carbon code out of
[graphios](), and thought it might be useful to other engineers as a
stand-alone thing. I have a lot of work to do to make Gryphie into the thing I
actually want to use myself. It needs meaningful documentation, Go and Ruby
support, features beyond writing so it can export series from the various
backends, and more advanced api features like Librato Annotation support.  But
if you're working in Python, and you just want to push metrics, Gryphie works
pretty well today, and its write interface shouldn't change all that much
(famous last words). 

#### What about project-X ?
Gryphie isn't a monitoring tool. It's a tool for people who work on monitoring
tools. So, for example, if you want to quickly write an export plug-in for
Tool-X, so that Tool-X can talk to Graphite, you could use Gryphie to implement
your plugin.  
