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
from time import mktime


class ServerThread(Thread):

    def __init__(self, octopasty, channel, details):
        Thread.__init__(self)
        self.octopasty = octopasty
        self.channel = channel
        self.details = details
        self.id = int(mktime(datetime.now().timetuple()))

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

    def handle_line(self):
        line = self.file.readline()
        if len(line) == 0:
            self.set_disconnected()
        else:
            print "[%s] <= %s" % (self.id, line.strip())


class MainListener(Thread):

    def __init__(self, octopasty):
        Thread.__init__(self)
        self.octopasty = octopasty
        self.start()

    def run(self):
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
            self.octopasty.clients.add(st)
