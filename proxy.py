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
# import os
import socket
import sys
from threading import Thread
from importlib import reload
from collections import defaultdict
import tfparser as parser

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

    def run(self):
        """Receive packets from the server and run them through the parser module.

        When the start() method is called on a class instance, this code is run in a
        separate thread.

        """
        while True:
            data = self.server.recv(4096)
            if data:
                # print("[{}] <- {}".format(self.port, binascii.hexlify(data[:100])))
                try:
                    reload(parser)
                    parser.parse(data, "server", PERSISTENT_DATA)
                except Exception as exception:
                    print("server[{}]".format(self.port), exception)
                # forward to client
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

    def run(self):
        """Receive packets from the client and run them through the parser module."""
        while True:
            data = self.game.recv(4096)
            if data:
                # print("[{}] -> {}".format(self.port, binascii.hexlify(data[:100])))
                try:
                    reload(parser)
                    parser.parse(data, "client", PERSISTENT_DATA)
                except Exception as exception:
                    print("client[{}]".format(self.port), exception)
                # forward to server
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
            print("[proxy({})] setting up".format(self.port))
            self.g2p = Game2Proxy(self.from_host, self.port)  # waiting for a client
            self.p2s = Proxy2Server(self.to_host, self.port)
            print("[proxy({})] connection established".format(self.port))
            self.g2p.server = self.p2s.server
            self.p2s.game = self.g2p.game

            self.g2p.start()
            self.p2s.start()


def main():
    """Run the script."""
    proxy = Proxy(PROXY_IP, TF_SERVER, TF_PORT)
    proxy.start()

    # some simple input so user can inject commands, etc.
    while True:
        try:
            cmd = input("$ ")
            if cmd[:4] == "quit":
                sys.exit()
                # os._exit(0)
        except Exception as exception:
            print(exception)


if __name__ == "__main__":
    main()
