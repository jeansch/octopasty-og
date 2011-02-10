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


from time import sleep
from datetime import datetime, timedelta
from Queue import Queue

from amiclient import AMIClient
from server import MainListener
from squirm import squirm, burials
from allios import readall, sendall
from config import read_config
from utils import tmp_debug

_1S = timedelta(0, 1)
_10S = timedelta(0, 10)


class Octopasty(object):

    def __init__(self, config_filename):
        self.config = read_config(config_filename)
        self.servers = self.config.get('amis')
        self.connect_tentatives = dict()
        self.amis = dict()
        self.clients = dict()
        self.in_queue = Queue()
        self.out_queue = Queue()
        self.flow = dict()
        self.listener = None

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
                filter(lambda _ami: _ami.connected, self.amis.values())]
    connected_servers = property(_get_connected_servers)

    def _get_ami_sockets(self):
        return [ami.socket for ami in \
                filter(lambda _ami: _ami.connected, self.amis.values())]
    ami_sockets = property(_get_ami_sockets)

    # Client side
    def listen_clients(self):
        self.listener = MainListener(self)

    def _get_connected_clients(self):
        return [client.id for client in \
                filter(lambda _client: _client.connected,
                       self.clients.values())]
    connected_clients = property(_get_connected_clients)

    def _get_client_sockets(self):
        return [client.socket for client in \
                filter(lambda _client: _client.connected,
                       self.clients.values())]
    client_sockets = property(_get_client_sockets)

    def _get_peers(self):
        return list(self.clients.values()) + list(self.amis.values())
    peers = property(_get_peers)

    def find_peer_from_socket(self, s):
        for peer in self.peers:
            if peer.socket == s:
                return peer
        return None

    def get_peer(self, name):
        return self.amis.get(name) or self.clients.get(name) or None

    def idle(self):
        if len(self.connected_servers) == 0 and \
               len(self.connected_clients) == 0:
            sleep(1)

    def loop(self):
        looping = True
        self.listen_clients()
        while looping:
            try:
                self.connect_servers()
                self.idle()
                readall(self)
                squirm(self)
                burials(self)
                sendall(self)
            except KeyboardInterrupt:
                for ami in self.amis.values():
                    tmp_debug("NETWORK", "Disconecting from %s" % ami.uid)
                    ami.disconnect()
                    ami.join()
                for client in self.clients.values():
                    tmp_debug("NETWORK", "Disconecting %s" % client.uid)
                    client.disconnect()
                    client.join()
                looping = False
        self.listener.stop()
        self.listener.join()
