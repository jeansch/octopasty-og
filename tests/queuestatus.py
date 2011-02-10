#!/usr/bin/python

from Asterisk import Manager


if __name__ == '__main__':
    manager = Manager.Manager(('localhost', 4321),
                               'plop', "plop",
                               listen_events=False)

    qs = manager.QueueStatus()
    for k in manager.QueueStatus():
        print "%s" % (k)
