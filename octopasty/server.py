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
from time import sleep, time
from asterisk import Action
from asterisk import STARTING_EVENTS_KEYWORDS

from utils import Packet, bigtime
from utils import deprotect, tmp_debug


class ServerThread(Thread):

    def __init__(self, octopasty, channel, details):
        Thread.__init__(self)
        self.octopasty = octopasty
        self.channel = channel
        self.details = details
        self.action = None
        self.logged = False
        self.id = 'unknown_%d' % bigtime()
        self.locked = 0
        self.wants_events = False
        self.binded_server = None
        self.keep_flow = False

    def disconnect(self):
        if self.channel:
            self.channel.close()
            self.channel = None
        if self.id in self.octopasty.clients:
            self.octopasty.clients.pop(self.id)
        self.connected = False
        self.file = None

    def run(self):
        self.file = self.channel.makefile()
        self.connected = True
        self.file.write("Asterisk Call Manager/1.1\r\n")
        self.file.flush()
        self.octopasty.clients.update({self.id: self})

    def send(self, packet):
        released_lock = None
        if self.locked:
            if packet.locked == self.locked:
                tmp_debug("%s => %s" % (self.uid,
                                        deprotect(packet.packet)))
                self.file.write(packet.packet)
                self.file.flush()
                released_lock = self.locked
                if not self.keep_flow:
                    self.locked = 0
            else:
                # just discard, may be too old
                pass
        else:
            # on let events go
            if not packet.locked:
                self.file.write(packet.packet)
                self.file.flush()
            else:
                # humm, why we get that ??
                pass
        return released_lock

    def handle_line(self):
        can_read = False
        if self.channel:
            can_read = True
            self.channel.setblocking(0)
        while can_read and self.file:
            try:
                line = self.file.readline()
                if len(line) == 0:
                    self.disconnect()
                else:
                    tmp_debug("%s <= %s" % (self.uid, deprotect(line)))
                    line = line.strip()
                    # if locked, we are waiting for a result
                    if not self.locked:
                        if line.lower().startswith('action:'):
                            self.action = \
                                     Action(line[line.find(':') + 1:].strip())
                        elif line == '':
                            if self.action:
                                self.locked = bigtime()
                                self.push(self.action)
                                self.action = None
                        else:
                            if ':' in line:
                                k = line.split(':')[0]
                                v = line[line.find(':') + 1:].strip()
                            if self.action:
                                self.action.add_parameters({k: v})
            except socket.error:
                can_read = False
        if self.channel:
            self.channel.setblocking(1)

    def push(self, packet):
        if packet.name.lower() in STARTING_EVENTS_KEYWORDS:
            self.keep_flow = True
        p = dict(emiter=self.id, locked=self.locked,
                 timestamp=time(), packet=packet)
        self.octopasty.in_queue.put(Packet(p))

    def _get_available(self):
        return self.connected and not self.locked
    available = property(_get_available)

    def _get_uid(self):
        return self.id
    uid = property(_get_uid)


class MainListener(Thread):

    def __init__(self, octopasty):
        Thread.__init__(self)
        self.octopasty = octopasty
        self.start()

    def run(self):
        while True:
            try:
                server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                server.bind((self.octopasty.config.get('bind_address'),
                             int(self.octopasty.config.get('bind_port'))))
                print "Listening on %s %s" % \
                      (self.octopasty.config.get('bind_address'),
                       self.octopasty.config.get('bind_port'))
                server.listen(5)
                while True:
                    channel, details = server.accept()
                    st = ServerThread(self.octopasty, channel, details)
                    st.start()
            except socket.error, e:
                print "%s trying to bind on %s %s" % \
                      (e, self.octopasty.config.get('bind_address'),
                       self.octopasty.config.get('bind_port'))
                sleep(10)
