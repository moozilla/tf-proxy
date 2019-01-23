"""Create a network proxy to sniff Tetris Friends network traffic.

This script establishes a simple TCP network proxy between the Tetris Friends server and
client, that can be used to sniff traffic, as well as inject traffic. Possible uses:
* Record games as they are being played, to create a large corpus of game play data
  (eg. for training a ML model)
* Generate live stats on player performance, and inject chat message summaries
* Experiment with undocumented parts of the game

Based on LiveOverflow's code here:
https://github.com/LiveOverflow/PwnAdventure3/tree/master/tools/proxy

For this to work you will need to route "sfs.tetrisfriends.com" to localhost in your
/etc/hosts file.

"""
# import binascii
import os
import socket
from threading import Thread
from importlib import reload
from collections import defaultdict, deque
import tfparser as parser

NULL_BYTE = b"\x00"

# This is the IP for sfs.tetrisfriends.com
TF_SERVER = "50.56.1.203"
TF_PORT = 9339
# Use localhost by default, change this if running proxy on a different IP
PROXY_IP = "0.0.0.0"

# initialize a dictionary here to for the parser to use, since we are constantly
# reloading the module  we need some data to persist outside of the parser module
PERSISTENT_DATA = {"fields": defaultdict(list), "game_started": False}


class Proxy2Server(Thread):
    """This class creates a connection from the game server to the proxy."""

    def __init__(self, host, port):
        """Initialize the connection to the server."""
        super(Proxy2Server, self).__init__()
        self.game = None  # game client socket not known yet
        self.port = port
        self.host = host
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.connect((host, port))
        self.queue = deque()

    def run(self):
        """Receive packets from the server and run them through the parser module.

        When the start() method is called on a class instance, this code is run in a
        separate thread.

        """
        buffer = b""
        while True:
            # not sure if this should send one per packet or all at once
            while self.queue:
                packet = self.queue.popleft()
                print("sending packet to client:", packet)
                self.game.sendall(packet)
            data = self.server.recv(4096)
            if data:
                buffer += data
                while NULL_BYTE in buffer:
                    packet, _, buffer = buffer.partition(NULL_BYTE)
                    # could make this return if we should suppress
                    process_packet(packet, "server")
                # forward data to game, do this after processing, in case we want to
                # suppress sending data later
                self.game.sendall(data)


class Game2Proxy(Thread):
    """This class creates a connection from the game client to the proxy."""

    def __init__(self, host, port):
        """Initialize the connection to the client."""
        super(Game2Proxy, self).__init__()
        self.server = None  # real server socket not known yet
        self.port = port
        self.host = host
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.listen(1)
        # waiting for a connection
        self.game, _ = sock.accept()
        self.queue = deque()

    def run(self):
        """Receive packets from the client and run them through the parser module."""
        buffer = b""
        while True:
            while self.queue:
                packet = self.queue.popleft()
                print("sending packet to server:", packet)
                self.server.sendall(packet)
            data = self.game.recv(4096)
            if data:
                buffer += data
                while NULL_BYTE in buffer:
                    packet, _, buffer = buffer.partition(NULL_BYTE)
                    process_packet(packet, "client")
                # forward data to server, do this after processing, in case we want to
                # suppress sending data later
                self.server.sendall(data)


class Proxy(Thread):
    """This class serves as a bridge between the client and server."""

    def __init__(self, from_host, to_host, port):
        """Initialize the proxy."""
        super(Proxy, self).__init__()
        self.from_host = from_host
        self.to_host = to_host
        self.port = port
        self.g2p = None
        self.p2s = None

    def run(self):
        """Create the two proxy connections and set up the bridge."""
        while True:
            print("[proxy({})] setting up - waiting for connection".format(self.port))
            self.g2p = Game2Proxy(self.from_host, self.port)  # waiting for a client
            self.p2s = Proxy2Server(self.to_host, self.port)
            print("[proxy({})] connection established".format(self.port))
            self.g2p.server = self.p2s.server
            self.p2s.game = self.g2p.game

            self.g2p.start()
            self.p2s.start()


def process_packet(packet, origin):
    """Process a packet of data.

    This is a shared wrapper for processing data from both client and server.

    :param packet: bytes object representing binary data for one packet
    :param origin: string representing origin of packet, eg. "server"

    """
    try:
        # print(origin, packet)
        reload(parser)
        parser.parse(packet, origin, PERSISTENT_DATA)
    except Exception as exception:
        print(f"Error processing {origin} packet:", packet[:32], "…")
        print(repr(exception))


def main():
    """Run the script."""
    proxy = Proxy(PROXY_IP, TF_SERVER, TF_PORT)
    proxy.start()

    # some simple input so user can inject commands, etc.
    while True:
        try:
            cmd = input("$ ")
            if cmd[:1] == "q":
                # sys.exit doesn't work, there's probably a better way to do this
                os._exit(0)  # pylint: disable=W0212
            elif cmd[:1] == "s":
                # send packet to server (from client)
                packet = cmd[1:].encode() + NULL_BYTE
                proxy.g2p.queue.append(packet)
                print("c->s:", packet)
            elif cmd[:1] == "c":
                # send packet to client (from server)
                packet = cmd[1:].encode() + NULL_BYTE
                proxy.p2s.queue.append(packet)
                print("s->c:", packet)
        except Exception as exception:
            print(exception)


if __name__ == "__main__":
    main()
