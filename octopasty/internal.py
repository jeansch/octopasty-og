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


def handle_packet(self, packet):
    # TODO: Handle login

    # from client:
    # E: unknown1296257108,
    # T: 1296257114.41,
    # L: 0,
    # D: __internal__,
    # P: Action: login\nUsername: plop\n
    #    Secret: 64faf5d0b1dc311fd0f94af64f6c296a03045571\nEvents: on\n\n
    #
    # TODO: set binded_server, set logged,
    #       replace the 'unknowXXXXX' id (beware of multiple cx)
    #       check if it wants the events

    # from AMI:
    # E: vgw6
    # T: 1296257138.24
    # L: 12962570451093290
    # P: Action: Success\nMessage: Authentication accepted\n\n
    # TODO: set logged
    pass
