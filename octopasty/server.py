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
import errno
from asterisk import Action
from asterisk import STARTING_EVENTS_KEYWORDS

from utils import Packet, bigtime
from utils import deprotect, tmp_debug

LISTENING_TIMEOUT = 10


class ServerThread(Thread):

    def __init__(self, octopasty, channel, details):
        Thread.__init__(self)
        self.octopasty = octopasty
        self.socket = channel
        self.details = details
        self.action = None
        self.logged = False
        self.authtype = None
        self.multiple_servers = list()
        self.id = 'unknown_%d' % bigtime()
        self.locked = 0
        self.wants_events = False
        self.binded_server = None
        self.keep_flow = False
        self.buffer = ''
        self.lines = list()

    def disconnect(self):
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
            except:
                pass
        if self.id in self.octopasty.clients:
            self.octopasty.clients.pop(self.id)
        self.connected = False
        self.socket = None

    def run(self):
        self.connected = True
        self.socket.sendall("Asterisk Call Manager/1.1\r\n")
        self.octopasty.clients.update({self.id: self})

    def send(self, packet):
        released_lock = None
        if self.locked:
            if packet.locked == self.locked:
                tmp_debug("IO", "O => %s: %s" % (self.uid,
                                        deprotect(packet.packet)))
                try:
                    self.socket.sendall(str(packet.packet))
                except:
                    self.disconnect()
                    return None
                released_lock = self.locked
                if not self.keep_flow:
                    self.locked = 0
            else:
                # just discard, may be too old
                pass
        else:
            # on let events go
            if not packet.locked:
                tmp_debug("IO", "O => %s %s" % (self.uid,
                                        deprotect(packet.packet)))
                try:
                    self.socket.sendall(str(packet.packet))
                except:
                    self.disconnect()
            else:
                # humm, why we get that ??
                pass
        return released_lock

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
            tmp_debug("IO", "%s => O: %s" % (self.uid, deprotect(line)))
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
        self.lines = []

    def push(self, packet):
        if packet.name.lower() in STARTING_EVENTS_KEYWORDS:
            self.keep_flow = True
        p = dict(emiter=self.id, locked=self.locked,
                 timestamp=time(), packet=packet)
        tmp_debug("PACKET", "%s (L:%s, KF:%s) >> %s" % (self.uid, self.locked,
                                                        self.keep_flow,
                                                        deprotect(str(p))))
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
        self.octopasty.listener = self
        self.start()

    def run(self):
        self.listening = True
        while self.listening:
            try:
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.s.bind((self.octopasty.config.get('bind_address'),
                             int(self.octopasty.config.get('bind_port'))))
                tmp_debug("NETWORK", "Listening on %s %s" % \
                          (self.octopasty.config.get('bind_address'),
                           self.octopasty.config.get('bind_port')))
                self.s.listen(5)
                while self.listening:
                    channel, details = self.s.accept()
                    st = ServerThread(self.octopasty, channel, details)
                    st.start()
            except socket.error, e:
                if e.errno == errno.EADDRINUSE:
                    tmp_debug(
                        "NETWORK",
                        "Address already used trying to bind on %s %s" % \
                        (self.octopasty.config.get('bind_address'),
                         self.octopasty.config.get('bind_port')))
                    for timeout in range(0, LISTENING_TIMEOUT):
                        if self.listening == False:
                            break
                        sleep(1)
                elif e.errno == errno.EINVAL:
                    tmp_debug("NETWORK", "Closing server, time to sleep")
                    self.listening = False
                else:
                    tmp_debug("NETWORK", "Unknown socket error: %s" % e)
                    self.listening = False

    def stop(self):
        try:
            self.s.shutdown(socket.SHUT_RDWR)
        except:
            # happend with there is already a listener
            self.listening = False
