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

from ConfigParser import ConfigParser


def read_config(filename):
    _config = dict()
    _config['amis'] = dict()
    config = ConfigParser()
    config.read(filename)
    assert config.has_section("amis"), \
           "No 'amis' section in the config file"
    _amis = config.items('amis')
    assert len(_amis) > 0, "No AMIs configured"
    for key, parameters in _amis:
        left, right = parameters.split('@')
        user, password = left.split(':')
        host, port = right.split(':')
        _config['amis'][key] = dict(user=user, password=password,
                                       host=host, port=port)
    assert config.has_section("server"), \
           "No 'server' section in the config file"
    _config['bind_address'] = config.get('server', 'address')
    _config['bind_port'] = config.get('server', 'port')
    return _config
