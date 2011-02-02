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


class Packet(object):
    _name_ = 'Packet'

    def __init__(self, name=None, parameters=None):
        self.parameters = dict()
        self.name = name
        if self.name and parameters:
            self.add_parameters(parameters)

    def add_parameters(self, parameters):
        self.parameters.update(parameters)

    def __repr__(self):
        out = "Action: %s\n" % self.name
        for p in self.parameters:
            if self.parameters[p] == None:
                out += "%s\n" % p
                pass
            else:
                out += "%s: %s\n" % (p, self.parameters.get(p))
        out += "\n"
        return out


class Command(Packet):
    _name_ = 'Command'
    pass


class Login(Command):
    _name_ = 'Login'

    def __init__(self, login, password):
        Command.__init__(self, 'login', dict(Username=login,
                                             Secret=password,
                                             Events='on'))


class Answer(Packet):
    _name_ = 'Answer'


class Event(Answer):
    _name_ = 'Event'


class Response(Packet):
    _name_ = 'Response'


class Action(Answer):
    _name_ = 'Action'


class Success(Action):
    _name_ = 'Success'

    def __init__(self, parameters):
        Action.__init__(self, 'Success', parameters)


class Error(Action):
    _name_ = 'Error'

    def __init__(self, parameters):
        Action.__init__(self, 'Error', parameters)
