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


def readall(self):
    reading = self.ami_files + self.client_files
    if len(reading) > 0:
        to_read, _, _ = select(reading, [], [], 1)
        for f in to_read:
            peer = self.find_peer_from_file(f)
            peer.handle_line()


def sendall(self):
    if not self.out_queue.empty:
        outgoing = list(self.queue.queue)
        self.queue.queue.clear()
        for packet in outgoing:
            if packet.dest == '__internal__':
                pass
                # should be the login stuff
            else:
                dest = self.get_peer(packet.dest)
                sent = dest.send(packet)
                if sent:
                    if sent in self.flow:
                        self.flow.pop(sent)
                    else:
                        self.flow[sent] = packet.emiter


def burials(self):
    apocalypse = time() - 10
    # Remove old locks
    for peer in self.peers:
        if peer and peer.locked < apocalypse:
            peer.locked = 0


# The nervous central
# Thanks to Derek for the awesome function name !
def squirm(self):
    if not self.in_queue.empty:
        incoming = list(self.in_queue.queue)
        self.in_queue.queue.clear()
        for packet in incoming:
            if packet.emiter == '__internal__':
                dest = self.get_peer(packet.dest)
                if dest and dest.available:
                    self.out_queue.put(packet)
                else:
                    self.in_queue.put(packet)
            else:
                if packet.locked:
                    emiter = self.get_peer(packet.emiter)
                    dest = self.flow.get(emiter.locked)
                    emiter.locked = 0
                    if dest:
                        packet.dest = dest
                        self.out_queue.put(packet)
                else:
                    # should be broadcast (events)
                    pass
