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

    def set_disconnected(self):
        if self.socket:
            self.socket.close()
            self.socket = None
        if self in self.octopasty.amis:
            self.octopasty.amis.remove(self)
        self.connected = False
        self.file = None

    def run(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.host, int(self.port)))
            self.socket = s
            self.octopasty.amis.add(self)
            self.connected = True
            self.file = self.socket.makefile()
        except socket.error:
            # May be log something one day
            pass

    def handle_line(self):
        line = self.file.readline()
        if len(line) == 0:
            self.set_disconnected()
        else:
            print "[%s] => %s" % (self.server, line.strip())