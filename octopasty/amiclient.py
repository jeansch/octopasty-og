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
from time import time
from utils import Packet, bigtime
from utils import deprotect, tmp_debug

from asterisk import Login
from asterisk import Event, Response


class AMIClient(Thread):
    def __init__(self, octopasty, server, parameters):
        Thread.__init__(self)
        self.octopasty = octopasty
        self.server = server
        self.socket = None
        self.host = parameters.get('host')
        self.port = parameters.get('port')
        self.user = parameters.get('user')
        self.password = parameters.get('password')
        self.connected = False
        self.file = None
        self.response = None
        self.event = None
        self.logged = False
        self.locked = False

    def disconnect(self):
        if self.socket:
            self.socket.close()
            self.socket = None
        if self.server in self.octopasty.amis:
            self.octopasty.amis.pop(self.server)
        self.connected = False
        self.file = None

    def send(self, packet):
        if not self.locked:
            tmp_debug("%s => %s" % (self.uid,
                                    deprotect(packet.packet)))
            self.file.write(packet.packet)
            self.file.flush()
            self.locked = packet.locked
            return self.locked
        else:
            return None

    def login(self):
        self.push(Login(self.user, self.password),
                  emiter='__internal__', dest=self.server,
                  locked=bigtime())

    def run(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.host, int(self.port)))
            self.socket = s
            self.octopasty.amis.update({self.server: self})
            self.connected = True
            self.file = self.socket.makefile(bufsize=42)
        except socket.error:
            pass

    def handle_line(self):
        can_read = False
        if self.socket:
            can_read = True
            self.socket.setblocking(0)
        while can_read and self.file:
            try:
                line = self.file.readline()
                if len(line) == 0:
                    self.disconnect()
                else:
                    tmp_debug("%s <= %s" % (self.uid, deprotect(line)))
                    line = line.strip()
                    if line.startswith('Asterisk Call Manager'):
                        self.login()
                        return
                    if self.locked and line.lower().startswith('response:'):
                        self.response = \
                                  Response(line[line.find(':') + 1:].strip())
                        self.event = None
                    elif line.lower().startswith('event:'):
                        self.event = Event(line[line.find(':') + 1:].strip())
                        self.response = None
                    elif line == '':
                        if self.response:
                            self.push(self.response)
                            self.response = None
                        elif self.event:
                            self.push(self.event)
                            self.event = None
                    else:
                        if ':' in line:
                            k = line.split(':')[0]
                            v = ':'.join(line.split(':')[1:]).lstrip()
                        else:
                            k = line
                            v = None
                        if self.response:
                            self.response.add_parameters({k: v})
                        if self.event:
                            self.event.add_parameters({k: v})
            except socket.error:
                can_read = False
        if self.socket:
            self.socket.setblocking(1)

    def push(self, packet, emiter=None, dest=None, locked=0):
        p = dict(emiter=emiter or self.server,
                 locked=locked or self.locked, timestamp=time(),
                 packet=packet)
        if dest:
            p['dest'] = dest
        self.octopasty.in_queue.put(Packet(p))

    def _get_available(self):
        return self.connected and not self.locked
    available = property(_get_available)

    def _get_uid(self):
        return self.server
    uid = property(_get_uid)
