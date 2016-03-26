#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  zmqpullin.py
#
#  Copyright 2016 Jelle Smet <development@smetj.net>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#


from wishbone import Actor
from wishbone.event import Event
import zmq.green as zmq


class ZMQPullIn(Actor):

    '''**Pulls events from one or more ZeroMQ push modules.**

    Expects to connect with one or more wishbone.input.push modules.  This
    module can be started in client or server mode.  In server mode, it waits
    for incoming connections.  In client mode it connects to the defined
    servers.  Events are spread in a round robin pattern over all connections.

    Parameters:

        - mode(str)("server")
           |  The mode to run in.  Possible options are:
           |  - server: Binds to a port and listens.
           |  - client: Connects to a port.

        - interface(string)("0.0.0.0")
           |  The interface to bind to in server <mode>.

        - port(int)(19283)
           |  The port to bind to in server <mode>.

        - servers(list)([])
           |  A list of hostname:port entries to connect to.
           |  Only valid when running in "client" <mode>.


    Queues:

        - outbox
           |  Events arriving from the outside.

    '''

    def __init__(self, actor_config, mode="server", interface="0.0.0.0", port=19283, servers=[]):
        Actor.__init__(self, actor_config)
        self.pool.createQueue("outbox")

    def preHook(self):

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PULL)

        if self.kwargs.mode == "server":
            self.socket.bind("tcp://*:%s" % self.kwargs.port)
            self.logging.info("Listening on port %s" % (self.kwargs.port))
        else:
            self.socket.connect("tcp://%s" % self.kwargs.servers[0])

        self.sendToBackground(self.drain)

    def drain(self):

        while self.loop():
            data = self.socket.recv()
            event = Event(data)
            self.submit(event, self.pool.queue.outbox)
