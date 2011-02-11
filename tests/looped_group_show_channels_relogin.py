#!/usr/bin/python
import sys

from Asterisk import Manager
from datetime import datetime

if __name__ == '__main__':
    manager = Manager.Manager(('localhost', 4321),
                              sys.argv[1], "plop",
                              listen_events=False)
    lap = datetime.now()
    while True:
        manager = Manager.Manager(('localhost', 4321),
                                  sys.argv[1], "plop",
                                  listen_events=False)
        ret = manager.Command("group show channels")[2:-1]
        newlap = datetime.now()
        print "%s %s %s" % (newlap, newlap - lap, ret)
        lap = datetime.now()
