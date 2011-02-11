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

# must be lowercased
STARTING_EVENTS_KEYWORDS = ['queuestatus']
STOPPING_EVENTS_KEYWORDS = ['queuestatuscomplete']


class MetaPacket(object):
    _name_ = 'MetaPacket'
    _direction_ = 'Action'

    def __init__(self, name=None, parameters=None):
        self.parameters = dict()
        self.parameters_order = list()
        self.name = name or self._name_
        if self.name and parameters:
            self.add_parameters(parameters)

    def add_parameters(self, parameters):
        self.parameters.update(parameters)
        self.parameters_order.extend(parameters.keys())

    def __repr__(self):
        out = "%s: %s\r\n" % (self._direction_, self.name)
        for p in self.parameters_order:
            if self.parameters[p] == None:
                out += "%s\n" % p
                pass
            else:
                out += "%s: %s\r\n" % (p, self.parameters.get(p))
        out += "\r\n"
        return out


# main classes
class Event(MetaPacket):
    _name_ = 'Event'
    _direction_ = 'Event'


class Response(MetaPacket):
    _name_ = 'Response'
    _direction_ = 'Response'


class Action(MetaPacket):
    _name_ = 'Action'


# real things
class Login(Action):
    _name_ = 'Login'

    def __init__(self, login, password):
        Action.__init__(self, parameters=dict(Username=login,
                                               Secret=password,
                                               Events='on'))


class Success(Response):
    _name_ = 'Success'


class Error(Response):
    _name_ = 'Error'


class Goodbye(Response):
    _name_ = 'Goodbye'
