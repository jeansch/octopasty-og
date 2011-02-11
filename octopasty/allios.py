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
from internal import handle_action
from asterisk import STOPPING_EVENTS_KEYWORDS
from utils import tmp_debug, deprotect


def readall(self):
    reading = self.ami_sockets + self.client_sockets
    if len(reading) > 0:
        # it's a timeout, that means that 0 != None
        timeout = self.out_queue.empty() and 0.1 or 0
        to_read, _, _ = select(reading, [], [], timeout)
        for s in to_read:
            peer = self.find_peer_from_socket(s)
            peer.handle_line()


def sendall(self):
    if not self.out_queue.empty():
        outgoing = list(self.out_queue.queue)
        self.out_queue.queue.clear()
        for packet in outgoing:
            tmp_debug("PACKET", "%s << %s" % (packet.dest, deprotect(packet)))
            if packet.dest == '__internal__':
                handle_action(self, packet)
            else:
                dest = self.get_peer(packet.dest)
                if dest:
                    # here is another place to check
                    # and requeue if necessary
                    if packet.locked != dest.locked and \
                       not dest.available:
                        self.out_queue.put(packet)
                        tmp_debug("SQUIRM", "Requeueing on output: %s" % \
                                  deprotect(packet))
                        continue
                    if not packet.locked and not dest.available:
                        self.out_queue.put(packet)
                        tmp_debug("SQUIRM", "Requeueing on output: %s" % \
                                  deprotect(packet))
                        continue
                    sent = dest.send(packet)
                    if sent:
                        if str(sent) in self.flow:
                            keep_flow = dest.keep_flow
                            if packet.packet.name.lower() in \
                                   STOPPING_EVENTS_KEYWORDS:
                                keep_flow = False
                                dest.keep_flow = False
                                dest.locked = 0
                            # then it was an answer
                            if not keep_flow:
                                self.flow.pop("%s" % sent)
                        else:
                            # then it was a query
                            self.flow["%s" % sent] = packet.emiter
                    else:
                        # Then it was an event
                        pass
