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

from hashlib import sha1, md5
from time import time
from random import randint

from utils import Packet, bigtime, tmp_debug
from asterisk import Success, Error, Goodbye

KEEP_INTERNAL = ['logoff']


def handle_action(self, packet):

    action = packet.packet
    if action.name.lower() == 'error':
        # needs to handle errors, may be a timeout before next try
        login_failed_on_ami(self, packet.emiter)

    if action.name.lower() == 'success':
        logged_on_ami(self, packet.emiter)

    if action.name.lower() == 'challenge':
        k = filter(lambda k: k.lower() == 'authtype',
                   action.parameters.keys())
        k = k and k[0] or None
        if k:
            challenge(self, packet.emiter, packet.locked,
                      action.parameters.get(k).lower())

    if action.name.lower() == 'login':
        login = dict()
        for k in ['Username', 'Secret', 'Events', 'Key']:
            v = action.parameters.get(k) or \
                action.parameters.get(k.lower()) or \
                action.parameters.get(k.upper())
            login[k.lower()] = v
        auth_user(self, packet.emiter, packet.locked, login.get('username'),
                  login.get('secret') or login.get('key'),
                  (login.get('events') and \
                  login.get('events').lower() == 'off') and False or True)

    if action.name.lower() == 'logoff':
        logoff_user(self, packet)


def auth_user(self, emiter, locked, username, secret, wants_events):
    login_sucessfull = False
    client = self.clients.get(emiter)
    if username in self.config.get('users'):
        hashed = self.config.get('users').get(username).get('password')
        if client.authtype is None:
            if sha1(secret).hexdigest() == hashed:
                login_sucessfull = True
        elif client.authtype[0] == 'md5':
            key = client.authtype[1]
            _md5 = md5(key)
            _md5.update(self.config.get('users').get(username).get('password'))
            if secret == _md5.hexdigest():
                login_sucessfull = True
    if login_sucessfull:
        old_id = client.id
        client.id = '%s_%d' % (username, bigtime())
        self.clients.pop(old_id)
        self.clients.update({client.id: client})
        client.logged = True
        _servers = self.config.get('users').get(username).get('servers')
        _servers = [s.strip() for s in _servers.split(',')]
        if len(_servers) == 1:
            client.binded_server = _servers[0]
        else:
            client.multiple_servers = _servers
        client.wants_events = wants_events
        response = Success(parameters=dict(
            Message='Authentication accepted'))
        p = dict(emiter='__internal__',
                 locked=locked,
                 timestamp=time(),
                 packet=response,
                 dest=client.id)
        tmp_debug("AUTH", "'%s' logged successfully" % username)
        self.out_queue.put(Packet(p))
    else:
        response = Error(parameters=dict(Message='Authentication failed'))
        p = dict(emiter='__internal__',
                 locked=locked,
                 timestamp=time(),
                 packet=response,
                 dest=client.id)
        client.send(Packet(p))
        tmp_debug("AUTH", "'%s' failed to login" % username)
        client.disconnect()


def logoff_user(self, packet):
    client = self.clients.get(packet.emiter)
    response = Goodbye(parameters=dict(Message="Don't panic."))
    p = dict(emiter='__internal__',
             locked=packet.locked,
             timestamp=time(),
             packet=response,
             dest=client.id)
    client.send(Packet(p))
    tmp_debug("AUTH", "'%s' logout" % packet.emiter[:packet.emiter.find('_')])
    client.disconnect()


def login_failed_on_ami(self, _ami):
    tmp_debug("AUTH", "Login failed on '%s'" % _ami)


def logged_on_ami(self, _ami):
    tmp_debug("AUTH", "Logged on '%s'" % _ami)
    ami = self.amis.get(_ami)
    ami.logged = True


def challenge(self, emiter, locked, authtype):
    if authtype == 'md5':
        key = str(randint(100000000, 999999999))
        response = Success(parameters=dict(
            Challenge='%s' % key))
        tmp_debug("AUTH", "'%s' asked for '%s' challenge, sent '%s'" % \
                  (emiter, authtype, key))
    else:
        response = Error(parameters=dict(
            Message='Authentication type not supported'))
    client = self.clients.get(emiter)
    p = dict(emiter='__internal__',
             locked=locked,
             timestamp=time(),
             packet=response,
             dest=client.id)
    client.send(Packet(p))
    client.authtype = (authtype, key)
