#!/usr/bin/python
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

from optparse import OptionParser

from octopasty import __version__
from octopasty.main import Octopasty


def main():
    parser = OptionParser(usage="%prog CONFIG_FILE",
                          description=__doc__,
                          version=__version__)
    args = parser.parse_args()[1]
    if len(args) < 1:
        parser.error("I need config file a config file as argument")
    o = Octopasty(args[0])
    o.loop()

if __name__ == '__main__':
    main()
