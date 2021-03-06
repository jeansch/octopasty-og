#!/usr/bin/python

import sys
from Asterisk import Manager
from datetime import datetime

if __name__ == '__main__':
    manager = Manager.Manager(('localhost', 4322),
                               sys.argv[1], "plop",
                               listen_events=False)
    lap = datetime.now()
    while True:
        try:
            ret = manager.QueueStatus()
        except KeyError, e:
            print "KeyError... %s" % e
            continue
        newlap = datetime.now()
        print "%s: %s events" % (newlap - lap, len(ret.keys()))
        lap = datetime.now()
