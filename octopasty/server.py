# -*- coding: utf-8 -*-

# Octopasty is an Asterisk AMI proxy

# Copyright (C) 2011  Jean Schurger <jean@schurger.org>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import socket
from threading import Thread
from datetime import datetime
from time import mktime, sleep
from asterisk import Action


class ServerThread(Thread):

    def __init__(self, octopasty, channel, details):
        Thread.__init__(self)
        self.octopasty = octopasty
        self.channel = channel
        self.details = details
        self.action = None
        self.logged = False
        self.id = 'unknown%d' % int(mktime(datetime.now().timetuple()))
        self.locked = 0
        self.wants_events = False

    def set_disconnected(self):
        if self.channel:
            self.channel.close()
            self.channel = None
        if self in self.octopasty.clients:
            self.octopasty.clients.remove(self)
        self.connected = False
        self.file = None

    def run(self):
        self.file = self.channel.makefile()
        self.connected = True
        self.file.write("Asterisk Call Manager/1.1\n")
        self.file.flush()

    def handle_line(self):
        line = self.file.readline()
        if len(line) == 0:
            self.set_disconnected()
        else:
            line = line.strip()
            if line.startswith('Action:'):
                self.action = Action(line.replace('Action: ', ''))
            elif line == '':
                if self.action:
                    self.push(self.action)
                    self.action = None
            else:
                if ':' in line:
                    k = line.split(':')[0]
                    v = ':'.join(line.split(':')[1:]).lstrip()
                if self.action:
                    self.action.add_parameters({k: v})

    def push(self, packet):
        self.octopasty.in_queue.put(dict(emiter=self.id,
                                         locked=self.locked,
                                         timestamp=datetime.now(),
                                         packet=packet,
                                         side='client'))


class MainListener(Thread):

    def __init__(self, octopasty):
        Thread.__init__(self)
        self.octopasty = octopasty
        self.start()

    def run(self):
        while True:
            try:
                server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                print "Try to bind on %s %s" % \
                      (self.octopasty.config.get('bind_address'),
                       self.octopasty.config.get('bind_port'))
                server.bind((self.octopasty.config.get('bind_address'),
                             int(self.octopasty.config.get('bind_port'))))
                print "Listening"
                server.listen(5)
                while True:
                    channel, details = server.accept()
                    st = ServerThread(self.octopasty, channel, details)
                    st.start()
                    self.octopasty.clients.add(st)
            except socket.error, e:
                print e
                sleep(10)
