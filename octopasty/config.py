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


def get_amis(config):
    ret = dict()
    ret['amis'] = dict()
    assert config.has_section("amis"), \
           "No 'amis' section in the config file"
    amis = config.items('amis')
    assert len(amis) > 0, "No AMIs configured"
    for key, parameters in amis:
        left, right = parameters.split('@')
        user, password = left.split(':')
        host, port = right.split(':')
        ret['amis'][key] = dict(user=user, password=password,
                                host=host, port=port)
    return ret


def get_server(config):
    ret = dict()
    assert config.has_section("server"), \
           "No 'server' section in the config file"
    ret['bind_address'] = config.get('server', 'address')
    ret['bind_port'] = config.get('server', 'port')
    return ret


def get_users(config):
    ret = dict()
    ret['users'] = dict()
    assert config.has_section("users"), \
           "No 'users' section in the config file"
    users = config.items('users')
    assert len(users) > 0, "No AMIs configured"
    for key, parameters in users:
        parameters = parameters.replace(' ', '')
        password, servers = parameters.split('@')
        user = key
        ret['users'][user] = dict(password=password,
                                  servers=servers)
    return ret


def read_config(filename):
    config = dict()
    parser = ConfigParser()
    parser.read(filename)
    config.update(get_amis(parser))
    config.update(get_server(parser))
    config.update(get_users(parser))
    return config
