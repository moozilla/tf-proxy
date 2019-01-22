"""Parse Tetris Friends network packets."""

# import binascii
import time
from xml.etree import ElementTree
from collections import defaultdict

import fumen
from snapshot import decode_snapshot

IGNORED_TAGS = ["policy-file-request", "cross-domain-policy"]
IGNORED_SYS_ACTS = ["verChk", "apiOK", "login", "autoJoin"]


def parse(packet_data, origin, persistent_data):
    """Parse data received in a packet.

    :param packet_data:     A bytes object representing the data received
    :param origin:          String representing origin of the packet, eg. "server"
    :param persistent_data: Dict used to persist data when module is reloaded

    """
    # decode packet data into string
    msg = packet_data.decode()

    # there are two types of packets, simple ones in this format:
    # %xt%arg%arg%
    if msg[0] == "%":
        percent_handler(msg.strip("%").split("%"), origin, persistent_data)
        return

    # and these more complicated ones that are XML
    parser = ElementTree.XMLParser(encoding="utf-8")
    elem = ElementTree.fromstring(msg, parser=parser)
    if elem.tag == "msg" and elem.attrib["t"] == "sys":
        body = elem[0]
        sys_handler(origin, body)
    elif elem.tag == "msg" and elem.attrib["t"] == "xt":
        # ignore these for now, probably use something like xthandler
        pass
    elif elem.tag in IGNORED_TAGS:
        pass
    else:
        print(f"unknown tag from {origin}:")
        print_elem(elem, max_depth=2)


def percent_handler(msg, origin, persistent_data):
    """Handle packets that start with a percent."""
    # fields object is defaultdict, passed in, used to persist frames
    if msg[0] == "xt":
        if msg[1] == "livePiece":
            # player placing a piece
            pass
        elif msg[1] == "snapShot":
            if not persistent_data["game_started"]:
                persistent_data["game_started"] = True
                persistent_data["start_time"] = time.perf_counter()
            try:
                room_id, player_id, snapshot = msg[2:]
                timestamp = time.perf_counter() - persistent_data["start_time"]
                comment = time.strftime("%M:%S", time.gmtime(timestamp))
                print(f"added frame for player {player_id} at {comment}")
                # create list of fumen frames to generate
                persistent_data["fields"][player_id].append(
                    (decode_snapshot(snapshot), comment)
                )
            except Exception as exception:
                # print(msg[2:])
                print("snapshot exception", exception)
        elif msg[1] == "results":
            # only output once
            if persistent_data["game_started"]:
                print("game ended")
                persistent_data["game_started"] = False

                for player, frames in persistent_data["fields"].items():
                    print("encoding fumen for player", player)
                    print(player, fumen.encode(frames))

                persistent_data["fields"] = defaultdict(list)  # reset fields
            # game end -- output fumens
        elif msg[1] == "resultsDone":
            # game start
            pass
        elif msg[1] == "TetrisLive":
            # also a results done
            pass
        elif msg[1] == "topOut":
            # player got topped out
            pass
        elif msg[1] == "zoneUserCount":
            # server telling us how many users are online
            # eg. ['zoneUserCount', '1', '243', '', '467315657']
            num_users = msg[3]
            num_games = msg[5]
            print(
                f"Logged in successfully. "
                f"{num_users} online, {num_games} games played."
            )
        else:
            # % packet is implied by square brackets
            print(f"{origin}:", msg[1:])
    else:
        print(f"unknown % packet from {origin}", msg)


def sys_handler(origin, body):
    """Parse msg tags where t= sys. Handlers are defined in SysHandler.as."""
    action = body.attrib["action"]
    if action == "uCount":
        # handleUserCountChange
        pass
        # room = body.attrib["r"]
        # users = body.attrib["u"]
        # # not defined for room 1, probably count in your rank?
        # spectators = body.attrib["s"] if "s" in body.attrib else None
        # print(
        #   f"== UserCountChange - Room: {room}, Users: {users}, "
        #  "Spectators: {spectators} =="
        # )
    elif action == "uER":
        # handleUserEnterRoom
        # print("UserEnterRoom")
        # printElem(body)
        # possible to set moderator?
        pass
    elif action == "uVarsUpdate":
        # handleUserVarsUpdate
        pass
    elif action == "roomAdd":
        # handleRoomAdded
        # some potentially interesting things here?
        pass
    elif action == "roomDel":
        # handleRoomDeleted
        pass
    elif action == "rmList":
        # server sends list of all the rooms
        pass
    elif action == "joinOK":
        # looks like list of all users in each room?
        pass
    elif action == "setUvars":
        # sending info about myself, could be interesting
        pass
    elif action in IGNORED_SYS_ACTS:
        pass
    else:
        # sys packet is implied by curly brackets
        print(f"{origin}:")
        print_elem(body, max_depth=2)


def print_elem(elem, depth=0, max_depth=10, max_children=3):
    """Recursively print out an XML tree for debugging."""
    padding = "".join(" " * depth)
    print(padding, "<" + elem.tag + ">", "attrib:", elem.attrib, "text:", elem.text)
    for child in elem[:max_children]:
        if depth >= max_depth:
            print(padding + "  …")
            break
        else:
            print_elem(child, depth=depth + 1, max_depth=max_depth)
    hidden_children = len(elem[max_children:])
    if hidden_children:
        print(padding, f" … {hidden_children} more children hidden")
