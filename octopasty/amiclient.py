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
from asterisk import STARTING_EVENTS_KEYWORDS
from asterisk import STOPPING_EVENTS_KEYWORDS


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
        self.response = None
        self.event = None
        self.logged = False
        self.authtype = None
        self.locked = False
        self.keep_flow = False
        self.buffer = ''
        self.lines = []

    def disconnect(self):
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
            except:
                pass
        if self.server in self.octopasty.amis:
            self.octopasty.amis.pop(self.server)
        self.connected = False
        self.socket = None

    def send(self, packet):
        if not self.locked:
            tmp_debug("IO", "O => %s: L: %s D: %s" % (
                self.uid,
                packet.locked,
                deprotect(packet.packet)))
            self.socket.sendall(str(packet.packet))
            if packet.packet.name.lower() in STARTING_EVENTS_KEYWORDS:
                self.keep_flow = True
                tmp_debug("PACKET", "%s Starting flow (L:%s)" % (self.uid,
                                                                 self.locked))
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
        except socket.error:
            pass

    def handle_line(self):
        if self.socket:
            bytes = ''
            try:
                bytes = self.socket.recv(4096)
            except:
                pass
            if len(bytes) == 0:
                self.disconnect()
            self.buffer += bytes
        in_lines = self.buffer.split('\n')
        self.lines.extend([l + '\n' for l in in_lines[:-1]])
        self.buffer = in_lines[-1]
        for line in self.lines:
            tmp_debug("IO", "%s => O: L: %s D: %s" % (
                self.uid, self.locked, deprotect(line)))
            line = line.strip()
            if line.startswith('Asterisk Call Manager'):
                self.login()
                self.lines = []
                return
            if self.locked and line.lower().startswith('response:'):
                self.response = \
                          Response(line[line.find(':') + 1:].strip())
                self.event = None
            elif line.lower().startswith('event:'):
                name = line[line.find(':') + 1:].strip()
                self.event = Event(name)
                self.response = None
            elif line == '':
                if self.response:
                    self.push(self.response)
                    self.response = None
                elif self.event:
                    if self.keep_flow:
                        self.push(self.event)
                    else:
                        self.push(self.event, locked=0)
                    self.event = None
            else:
                if ':' in line:
                    sc = line.find(':')
                    k = line[:sc].strip()
                    v = line[sc + 1:].strip()
                else:
                    k = line
                    v = None
                if self.response:
                    self.response.add_parameters({k: v})
                if self.event:
                    self.event.add_parameters({k: v})
        self.lines = []

    def push(self, packet, emiter=None, dest=None, locked=-1):
        p = dict(emiter=emiter or self.server,
                 locked=locked == -1 and self.locked or locked,
                 timestamp=time(),
                 packet=packet)
        if dest:
            p['dest'] = dest
        tmp_debug("PACKET", "%s (L:%s, KF:%s) >> %s" % (self.uid, self.locked,
                                                        self.keep_flow,
                                                        deprotect(p)))
        self.octopasty.in_queue.put(Packet(p))
        if packet.name.lower() in STOPPING_EVENTS_KEYWORDS:
            self.keep_flow = False
        tmp_debug("PACKET", "%s Stopping flow (L:%s)" % (self.uid,
                                                         self.locked))

    def _get_available(self):
        return self.connected and not self.locked
    available = property(_get_available)

    def _get_uid(self):
        return self.server
    uid = property(_get_uid)
