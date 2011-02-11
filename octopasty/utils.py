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

import os
from time import time
from datetime import datetime


class NiceDict(object):
    def __init__(self, entries):
        self.__dict__.update(entries)


class Packet(NiceDict):

    def __repr__(self):
        ret = ""
        ret += "E: %s, " % self.emiter
        ret += "T: %s, " % self.timestamp
        ret += "L: %s, " % self.locked
        if hasattr(self, 'dest'):
            ret += "D: %s, " % self.dest
        ret += "P: %s" % \
               str(self.packet).replace('\n', '\\n').replace('\r', '\\r')
        ret += "\n"
        return ret


def bigtime(delta=0):
    return int((time() + delta) * 10000000)


def deprotect(s):
    return str(s).replace('\r', '\\r').replace('\n', '\\n')


def tmp_debug(t, s):
    debug = os.environ.get('OCTOPASTY_DEBUG')
    debug = debug and debug.split(',') or []
    if t in debug:
        print "@%s [% 8s] %s" % (datetime.now(), t, s)
