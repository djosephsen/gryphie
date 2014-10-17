gryphie
=======

Gryphie makes it easy to wire that thing you're working on to the various
time-series storage and visualization systems like
[Graphite](http://graphite.readthedocs.org/en/latest/overview.html),
[InfluxDB](http://influxdb.com/), [Librato](http://metrics.librato.com), and
anything that supports [Statsd](https://github.com/etsy/statsd/)

With gryphie, your thing can emit metrics to any combination of these systems
simultaniously. You could, for example measure something, and then easily send
your measurement to two different Graphite systems, an Influx box and Librato.
At the moment Gryphie only works with python things, but soon it'll work with
Go and Ruby things too.

The general idea is that you instantiate a list of objects of the type that
knows how to talk to the backends you want, and keep them around in memory.
You pass each object a bit of configuration, when you first instantiate it.
Then, when you're ready to, for example, send a measurement to them, you just
call the object's .send() method, passing in the measurements you want to send.

Gryphie tries to wholly insulate you from wire protocol details, including
intricaceis like buffering/combining individual measuremnets to optomize
transport effeciency, and it tries to do this with a minimum of dependencies.
Gryphie's python implementation, for example, is built wholly on top of the
python standard library, and doesn't use any external dependencies at all. 

I have a lot of work to do with Gryphie, including meaningful documentation, Go
and Ruby support, support for reading things from the various backends, and
more advanced api features like Librato Annotation support.  But if you're
working in Python, and you just want to push metrics, Gryphie works pretty well
today, and its write interface shouldn't change all that much (famous last
words). 
