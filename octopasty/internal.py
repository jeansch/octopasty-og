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


def handle_action(self, packet):

    action = packet.packet
    if action.name.lower() == 'error':
        # needs to handle errors, may be a timeout before next try
        logged_on_ami(self, packet.emiter)

    if action.name.lower() == 'success':
        print "Logged successfully on %s" % packet.emiter

    if action.name.lower() == 'login':
        login = dict()
        for k in ['Username', 'Secret', 'Events']:
            v = action.parameters.get(k) or \
                action.parameters.get(k.lower()) or \
                action.parameters.get(k.upper())
            login[k.lower()] = v
        auth_user(self, packet.emiter, login.get('username'),
                  login.get('secret'),
                  login.get('events') and \
                  login.get('events').lower() == 'on' or False)


def auth_user(self, emiter, username, secret, events):
    print "%s try to login with %s %s %s" % \
          (emiter, username, secret, events)
    # TODO: set binded_server, set logged,
    #       replace the 'unknowXXXXX' id (beware of multiple cx)
    #       check if it wants the events
    # OK: Action: Success\nMessage: Authentication accepted\n\n
    # NOT OK: Action: Error\nMessage: Authentication failed\n\n
    pass


def logged_on_ami(self, ami):
    # set logged
    pass
