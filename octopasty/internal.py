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

from hashlib import sha1
from time import time

from utils import Packet, bigtime
from asterisk import Success, Error


def handle_action(self, packet):

    action = packet.packet
    if action.name.lower() == 'error':
        # needs to handle errors, may be a timeout before next try
        pass

    if action.name.lower() == 'success':
        logged_on_ami(self, packet.emiter)

    if action.name.lower() == 'login':
        login = dict()
        for k in ['Username', 'Secret', 'Events']:
            v = action.parameters.get(k) or \
                action.parameters.get(k.lower()) or \
                action.parameters.get(k.upper())
            login[k.lower()] = v
        auth_user(self, packet.emiter, packet.locked, login.get('username'),
                  login.get('secret'),
                  login.get('events') and \
                  login.get('events').lower() == 'on' or False)


def auth_user(self, emiter, locked, username, secret, wants_events):
    if username in self.config.get('users'):
        hashed = self.config.get('users').get(username).get('password')
        client = self.clients.get(emiter)
        if sha1(secret).hexdigest() == hashed:
            old_id = client.id
            client.id = '%s_%d' % (username, bigtime())
            self.clients.pop(old_id)
            self.clients.update({client.id: client})
            client.logged = True
            server = self.config.get('users').get(username).get('server')
            client.binded_server = server
            client.wants_events = wants_events
            action = Success(dict(Message='Authentication accepted'))
            p = dict(emiter='__internal__',
                     locked=locked,
                     timestamp=time(),
                     packet=action,
                     dest=client.id)
            self.out_queue.put(Packet(p))
        else:
            action = Error(dict(Message='Authentication failed'))
            p = dict(emiter='__internal__',
                     locked=locked,
                     timestamp=time(),
                     packet=action,
                     dest=client.id)
            client.send(Packet(p))
            client.disconnect()


def logged_on_ami(self, _ami):
    ami = self.amis.get(_ami)
    ami.logged = True
