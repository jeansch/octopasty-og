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

from select import select
from time import time
from copy import copy

from internal import handle_packet


def readall(self):
    reading = self.ami_files + self.client_files
    if len(reading) > 0:
        to_read, _, _ = select(reading, [], [], 1)
        for f in to_read:
            peer = self.find_peer_from_file(f)
            peer.handle_line()


def sendall(self):
    if len(list(self.out_queue.queue)):
        print "OUT: %s" % list(self.out_queue.queue)
    if not self.out_queue.empty():
        outgoing = list(self.out_queue.queue)
        self.out_queue.queue.clear()
        for packet in outgoing:
            if packet.dest == '__internal__':
                handle_packet(self, packet)
            else:
                dest = self.get_peer(packet.dest)
                sent = dest.send(packet)
                if sent:
                    if sent in self.flow:
                        # then it was an answer
                        self.flow.pop("%s" % sent)
                    else:
                        # then it was a query
                        self.flow["%s" % sent] = packet.emiter
                else:
                    # They it was an event
                    pass


def burials(self):
    apocalypse = int((time() - 10) * 10000000)
    # Remove old locks
    for peer in self.peers:
        if peer and peer.logged and peer.locked < apocalypse:
            peer.locked = 0


# The nervous central
# Thanks to Derek for the awesome function name !
def squirm(self):
    apocalypse = time() - 10
    if len(list(self.in_queue.queue)):
        print "IN: %s" % list(self.in_queue.queue)
    if not self.in_queue.empty():
        incoming = list(self.in_queue.queue)
        self.in_queue.queue.clear()
        for packet in incoming:
            if packet.timestamp < apocalypse:
                # not puting in the queue and just continuing
                # makes the packet go nowhere
                continue
            if packet.emiter == '__internal__':
                peer = self.get_peer(packet.dest)
                if peer and peer.available:
                    self.out_queue.put(packet)
                else:
                    self.in_queue.put(packet)
            else:
                if packet.locked:
                    emiter = self.get_peer(packet.emiter)
                    emiter.locked = 0
                    dest = self.flow.get("%s" % packet.locked)
                    if dest == '__internal__':
                        handle_packet(self, packet)
                    else:
                        peer = self.get_peer(dest)
                        if peer and peer.available and peer.logged:
                            packet.dest = dest
                            self.out_queue.put(packet)
                        else:
                            self.in_queue.put(packet)
                else:
                    if packet.emiter in self.connected_servers:
                        ami = self.get_peer(packet.emiter)
                        if ami.logged:
                            for client in self.connected_clients:
                                peer = self.get_peer(client)
                                if client.binded_server == packet.emiter and \
                                   client.wants_events:
                                    p = copy(packet)
                                    p.dest = client
                                    self.out_queue.put(p)
                        else:
                            # Do not remove that comment and that case
                            # it might be logged one day
                            # ami not logged, and no command before
                            # i wonder what can it be
                            pass
                    if packet.emiter in self.connected_clients:
                        client = self.get_peer(packet.emiter)
                        if client.logged:
                            cu = self.config['users'].get(client.id)
                            if cu:
                                cs = cu.get('server')
                                if cs:
                                    peer = self.get_peer(cs)
                                    if peer and peer.available and peer.logged:
                                        packet.dest = cs
                                        self.out_queue.put(packet)
                                    else:
                                        self.in_queue.put(packet)
                        else:
                            packet.dest = '__internal__'
                            self.out_queue.put(packet)
