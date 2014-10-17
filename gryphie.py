# vim: set ts=4 sw=4 tw=79 et :

import socket
import cPickle as pickle
import struct
import string
import re
import logging
import sys
import base64
import urllib2
import json
import os


class Measurement(object):
    def __init__(self):
        self.NAME = ''  # metric name 
        self.SOURCE = ''  # The source of the metric (used for librato source)
        self.VALUE = ''   # numerical value of the measurement
        self.TIME = ''    # The epoc time when the measurement was taken
    
    def __repr__(self):
        return "Name: %s, Source: %s, Value: %s, Time: %s" % (self.NAME,
        self.SOURCE, self.VALUE, self.TIME)


###########################################################
# #### Librato Backend
class librato(object):
    def __init__(self, cfg):
        """
        Implements the librato backend-module
        """

        self.log = logging.getLogger("log.backends.librato")
        self.log.info("Librato Backend Initialized")
        self.api = "https://metrics-api.librato.com"
        self.flush_timeout_secs = 5
        self.gauges = {}
        self.whitelist = []
        self.metrics_sent = 0
        self.max_metrics_payload = 500

        try:
            cfg["librato_email"]
        except:
            self.log.critical("please define librato_email")
            sys.exit(1)
        else:
            self.email = cfg['librato_email']

        try:
            cfg["librato_token"]
        except:
            self.log.critical("please define librato_token")
            sys.exit(1)
        else:
            self.token = cfg['librato_token']

        try:
            cfg["librato_floor_time_secs"]
        except:
            self.floor_time_secs = 10
        else:
            self.floor_time_secs = cfg["librato_floor_time_secs"]

        try:
            cfg["librato_whitelist"]
        except:
            self.whitelist = [re.compile(".*")]
        else:
            for pattern in cfg["librato_whitelist"]:
                self.log.debug("adding librato whitelist pattern %s" % pattern)
                self.whitelist.append(re.compile(pattern))

        try:
            uname = os.uname()
            system = "; ".join([uname[0], uname[4]])
        except:
            system = os.name()

        sink_name = "gryphie-librato"
        sink_version = "0.0.1"
        pver = sys.version_info
        self.user_agent = '%s/%s (%s) Python-Urllib2/%d.%d' % \
                     (sink_name, sink_version,
                      system, pver[0], pver[1])

        base64string = base64.encodestring('%s:%s' % (self.email, self.token))
        self.auth = base64string.translate(None, '\n')

        self.headers = {
            'Content-Type': 'application/json',
            'User-Agent': self.user_agent,
            'Authorization': 'Basic %s' % self.auth
        }

    def fix_path(self, m):
        path = ''

        try:
            m.SOURCE
        except:
            m.SOURCE = os.uname()[1]

        pdict=m.NAME.split('.')

        while m.SOURCE in pdict:
            pdict.remove(m.SOURCE)

        path = string.join(pdict)
        return path

    def not_in_whitelist(self, k):
        # return True if k isn't whitelisted
        wl_match = True
        for pattern in self.whitelist:
            if pattern.search(k) is not None:
                return False
        return True


    def add_measure(self, m):
        ts = float(m.TIME)
        if self.floor_time_secs is not None:
            ts = (ts / self.floor_time_secs) * self.floor_time_secs
        
        name = self.fix_path(m)
        source = m.SOURCE
                
        k = "%s\t%s" % (name, source)

        #bail if this metric isn't whitelisted
        if self.not_in_whitelist(k):
            return None

        #add the metric to our gauges dict
        if k not in self.gauges:
            self.gauges[k] = {
                'name': name,
                'source': source,
                'measure_time': ts,
            }

        value = float(m.VALUE)
        self.gauges[k]['value'] = value

    def post_payload(self, g):
        """
        POST a payload to Librato.
        """
        body = json.dumps({'gauges': g})
        url = "%s/v1/metrics" % (self.api)
        req = urllib2.Request(url, body, self.headers)

        try:
            f = urllib2.urlopen(req, timeout=self.flush_timeout_secs)
            f.close()
        except urllib2.HTTPError as error:
            self.metrics_sent = 0
            body = error.read()
            self.log.warning('Failed to send metrics to Librato: Code: \
                                %d . Response: %s' % (error.code, body))
        except IOError as error:
            self.metrics_sent = 0
            if hasattr(error, 'reason'):
                self.log.warning('Error when sending metrics Librato \
                                    (%s)' % (error.reason))
            elif hasattr(error, 'code'):
                self.log.warning('Error when sending metrics Librato \
                                    (%s)' % (error.code))
            else:
                self.log.warning('Error when sending metrics Librato \
                                    and I dunno why')


    def send(self, metrics):

        self.metrics_sent = len(metrics)
        # Construct the output
        for m in metrics:
            self.add_measure(m)

        # Nothing to do
        if len(self.gauges) == 0:
            return 0

        metrics = []
        count = 0
        for g in self.gauges.values():
            metrics.append(g)
            count += 1

            if count >= self.max_metrics_payload:
                self.post_payload(metrics)
                count = 0
                metrics = []

        if count > 0:
            self.post_payload(metrics)
            self.gauges = {}

        return self.metrics_sent


############################################################
# #### Carbon back-end #####

class carbon(object):
    def __init__(self, cfg):
        self.log = logging.getLogger("log.backends.carbon")
        self.log.info("Carbon Backend Initialized")

        self.carbon_servers=[]
        servers=''
        try:
            cfg['carbon_servers']
        except:
            self.carbon_servers = [{'127.0.0.1' : 2004}]
        else:
            serv = cfg['carbon_servers']
            if ":" in serv:
                s, p= serv.split(":")
                s = socket.gethostbyname(s)
                p = int(p)
            else:
                s = socket.gethostbyname(serv)
                p = 2004
            print("appending server:%s port:%s"%(s,p))
            self.carbon_servers.append({ s : p })

        try:
            cfg['replacement_character']
        except:
            self.replacement_character = '_'
        else:
            self.replacement_character = cfg['replacement_character']

        try:
            cfg['carbon_max_metrics']
            self.carbon_max_metrics = cfg['carbon_max_metrics']
        except:
            self.carbon_max_metrics = 200

        try:
            cfg['use_service_desc']
            self.use_service_desc = cfg['use_service_desc']
        except:
            self.use_service_desc = False

    def convert_pickle(self, metrics):
        """
        Converts the metric obj list into a pickle message
        """
        pickle_list = []
        messages = []
        for m in metrics:
            path = self.fix_string(m.NAME)
            value = m.VALUE
            timestamp = m.TIME
            metric_tuple = (path, (timestamp, value))
            pickle_list.append(metric_tuple)
        for pickle_list_chunk in self.chunks(pickle_list,
                                             self.carbon_max_metrics):
            payload = pickle.dumps(pickle_list_chunk)
            header = struct.pack("!L", len(payload))
            message = header + payload
            messages.append(message)
        return messages

    def chunks(self, l, n):
        """ Yield successive n-sized chunks from l.
        """
        for i in xrange(0, len(l), n):
            yield l[i:i + n]


    def fix_string(self, my_string):
        """
        takes a string and replaces whitespace and invalid carbon chars with
        the global replacement_character
        """
        invalid_chars = '~!@#$:;%^*()+={}[]|\/<>'
        my_string = re.sub("\s", self.replacement_character, my_string)
        for char in invalid_chars:
            my_string = my_string.replace(char, self.replacement_character)
        return my_string

    def send(self, metrics):
        """
        Connect to the Carbon server
        Send the metrics
        """
        ret = 0
        sock = socket.socket()
        for s in self.carbon_servers:
            print("parsing carbon_servers: %s"%s)
            server,port=s.items()[0]
            self.log.debug("Connecting to carbon at %s:%s" %
                          (server, port))
            try:
                sock.connect((server, port))
                self.log.debug("connected")
            except Exception, ex:
                self.log.warning("Can't connect to carbon: %s:%s %s" % (
                                 server, port, ex))

            messages = self.convert_pickle(metrics)
            try:
                for message in messages:
                    sock.sendall(message)
            except Exception, ex:
                self.log.critical("Can't send message to carbon error:%s" % ex)
            else:
                ret += 1
            sock.close()
        return ret


# ###########################################################
# #### statsd backend  #######################################

class statsd(object):
    def __init__(self, cfg):
        self.log = logging.getLogger("log.backends.statsd")
        self.log.info("Statsd backend initialized")

        servers=''
        self.statsd_servers=[]
        try:
            cfg['statsd_servers']
        except:
            self.statsd_servers = [{ '127.0.0.1' : 8125 }]
        else:
            serv=cfg['statsd_servers']
            if ":" in serv:
                s, p= serv.split(":")
                s = socket.gethostbyname(s)
                p = int(p)
            else:
                s = socket.gethostbyname(serv)
                p = 8125
            self.statsd_servers.append({ s : p })


    def convert(self, metrics):
        # Converts the metric object list into a list of statsd tuples
        out_list = []
        for m in metrics:
            value = "%s|g" % m.VALUE  # FIXME: you wanted a gauge right?
            metric_tuple = "%s:%s" % (m.NAME, value)
            out_list.append(metric_tuple)

        return out_list

    def send(self, metrics):
        # Fire metrics at the statsd server and hope for the best (loludp)
        ret = True
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        mlist = self.convert(metrics)
        ret = 0

        for s in self.statsd_servers:
            server, port = s.items()[0]
            self.log.debug("sending to statsd at %s:%s" %
                          (server, port))
            for m in mlist:
                try:
                    sock.sendto(m, (server, port))
                except Exception, ex:
                    self.log.critical("Can't send metric to statsd error:%s"
                                      % ex)
                else:
                    ret += 1

        return ret


# ###########################################################
# #### stdout backend  #######################################

class stdout(object):
    def __init__(self, cfg):
        self.log = logging.getLogger("log.backends.stdout")
        self.log.info("STDOUT Backend Initialized")

    def send(self, metrics):
        ret = 0
        print("-------")
        for metric in metrics:
            ret += 1
            print(metric)
            print("-------")

        return ret


# ###########################################################
# #### start here  #######################################

if __name__ == "__main__":
    print("I'm just a lowly module")
    sys.exit(42)
