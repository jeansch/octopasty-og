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
from time import sleep
from threading import Thread
from datetime import datetime, timedelta
from select import select

from amiclient import AMIClient

__version__ = 'Octopasty 0.1'

_1S = timedelta(0, 1)


class Octopasty(object):

    def __init__(self, config):
        self.servers = config.get('servers')
        self.clients = set()
        self.connect_tentatives = dict()
        self.amis = set()
        self.clients = []

    # AMI side
    def connect_server(self, server):
        parameters = self.servers.get(server)
        client = AMIClient(self, server, parameters)
        client.start()

    def connect_servers(self):
        now = datetime.now()
        connected_servers = self.connected_servers
        for server in self.servers:
            if server not in connected_servers:
                last_try = self.connect_tentatives.get(server)
                if last_try is None or \
                   now - last_try > _1S:
                    self.connect_tentatives[server] = now
                    self.connect_server(server)

    def _get_connected_servers(self):
        return [ami.server for ami in \
                filter(lambda _ami: _ami.connected, self.amis)]
    connected_servers = property(_get_connected_servers)

    def _get_ami_files(self):
        return [ami.file for ami in \
                filter(lambda _ami: _ami.connected, self.amis)]
    ami_files = property(_get_ami_files)

    # Client side
    def listen_clients(self):
        pass

    def _get_connected_clients(self):
        return []
    connected_clients = property(_get_connected_clients)

    def _get_client_files(self):
        return [client.file for client in \
                filter(lambda _client: _client.connected, self.clients)]
    client_files = property(_get_client_files)

    def find_client_from_file(self, file_):
        for ami in self.amis:
            if ami.file == file_:
                return ami
        return None

    def loop(self):
        while True:
            self.connect_servers()
            self.listen_clients()
            # don't eat the CPU for nothing
            if len(self.connected_servers) == 0 and \
               len(self.connected_clients) == 0:
                print "nothing connected, waiting..."
                sleep(1)
            # the big select (all blocking is here)
            reading = self.ami_files + self.client_files
            if len(reading) > 0:
                toread, _, _ = select(reading, [], [])
                for f in toread:
                    ami = self.find_client_from_file(f)
                    if ami:
                        ami.handle_line()
