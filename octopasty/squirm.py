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


from utils import bigtime
from time import time
from copy import copy

from utils import Packet, tmp_debug, deprotect
from asterisk import Error
from internal import handle_action, KEEP_INTERNAL


def burials(self):
    apocalypse = bigtime(-10)
    for peer in self.peers:
        if peer and peer.locked and peer.logged and peer.locked < apocalypse:
            peer.locked = 0
            tmp_debug("SQUIRM", "Removing the very old lock of  %s" % \
                      peer.uid)


# The nervous central
# Thanks to Derek for the awesome function name !
def squirm(self):
    apocalypse = time() - 10
    if not self.in_queue.empty():
        incoming = list(self.in_queue.queue)
        self.in_queue.queue.clear()
        for packet in incoming:
            tmp_debug("SQUIRM", "Processing packet %s" % deprotect(packet))
            if packet.timestamp < apocalypse:
                # not puting in the queue and just continuing
                # makes the packet go nowhere
                # TODO: figure what to do here, i was thinking about something
                # if packet.locked:
                #     dest = self.flow.get("%s" % packet.locked)
                #     if dest != '__internal__':
                #         peer = self.get_peer(dest)
                tmp_debug("SQUIRM", "Removing very old packet: %s" % packet)
                continue
            if packet.emiter == '__internal__':
                peer = self.get_peer(packet.dest)
                if peer and peer.available:
                    self.out_queue.put(packet)
                else:
                    self.in_queue.put(packet)
            else:
                if packet.locked:
                    if packet.emiter in self.connected_servers:
                        tmp_debug("SQUIRM", "Emiter is server %s" % \
                                  packet.emiter)
                        emiter = self.get_peer(packet.emiter)
                        if emiter.locked and not emiter.keep_flow:
                            emiter.locked = 0
                            tmp_debug("SQUIRM", "Unlocking emiter %s" % \
                                      emiter.uid)
                        dest = self.flow.get("%s" % packet.locked)
                        if dest:
                            if dest == '__internal__':
                                handle_action(self, packet)
                            else:
                                peer = self.get_peer(dest)
                                if peer and peer.logged:
                                    if peer.locked:
                                        if peer.locked == packet.locked:
                                            packet.dest = dest
                                            self.out_queue.put(packet)
                                        else:
                                            tmp_debug("SQUIRM",
                                                      "Requeueing packet " \
                                                      "from server: %s" % \
                                                      deprotect(packet))
                                            self.in_queue.put(packet)
                                else:
                                    # just forgot it, and stop flow if any
                                    if emiter.keep_flow:
                                        emiter.keep_flow = 0
                                        emiter.locked = 0
                        else:
                            if emiter.keep_flow:
                                emiter.keep_flow = 0
                                emiter.locked = 0
                    if packet.emiter in self.connected_clients:
                        tmp_debug("SQUIRM", "Emiter is client %s" % \
                                  packet.emiter)
                        if packet.packet.name.lower() in KEEP_INTERNAL:
                            handle_action(self, packet)
                            continue
                        client = self.get_peer(packet.emiter)
                        if client.logged:
                            cid = client.id.split('_')[0]
                            cu = self.config['users'].get(cid)
                            if cu:
                                cs = client.binded_server
                                if cs:
                                    peer = self.get_peer(cs)
                                    if peer and peer.logged:
                                        if peer.available:
                                            # server seems already available
                                            # but may be busy just after,
                                            # then we need to verify that
                                            # in outgoing packets too
                                            packet.dest = cs
                                            self.out_queue.put(packet)
                                            tmp_debug("SQUIRM",
                                                      "Packet from client " \
                                                      "pushed to queue %s" % \
                                                      deprotect(packet))
                                        else:
                                            # server seems busy
                                            self.in_queue.put(packet)
                                            tmp_debug("SQUIRM",
                                                      "Requeueing packet from "
                                                      " client: %s" % \
                                                      deprotect(packet))
                                    else:
                                        response = Error(
                                            parameters=dict(
                                                Message='Server unavailable'))
                                        p = dict(emiter=cs,
                                                 locked=packet.locked,
                                                 timestamp=time(),
                                                 packet=response,
                                                 dest=client.id)
                                        self.out_queue.put(Packet(p))
                                else:
                                    if len(client.multiple_servers):
                                        response = Error(
                                            parameters=dict(
                                                Message='Cannot send command '
                                                'to multiple servers'))
                                        p = dict(emiter='__internal__',
                                                 locked=packet.locked,
                                                 timestamp=time(),
                                                 packet=response,
                                                 dest=client.id)
                                        self.out_queue.put(Packet(p))
                        else:
                            packet.dest = '__internal__'
                            self.out_queue.put(packet)
                else:
                    # packet not locked
                    if packet.emiter in self.connected_servers:
                        # broadcast events
                        ami = self.get_peer(packet.emiter)
                        if ami.logged:
                            for client in self.connected_clients:
                                peer = self.get_peer(client)
                                if peer.binded_server == packet.emiter or \
                                   packet.emiter in peer.multiple_servers and \
                                   peer.wants_events:
                                    p = copy(packet)
                                    p.dest = client
                                    self.out_queue.put(p)
                        else:
                            # Do not remove that comment and that case
                            # it might be logged one day
                            # ami not logged, and no command before
                            # i wonder what can it be
                            pass
