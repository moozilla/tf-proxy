import binascii
import time
from xml.etree import ElementTree
from collections import defaultdict

import fumen
from snapshot import decode_snapshot


def parse(data, port, origin, persistent_data):
    # if origin == "server":
    #     return
    # print("[{}({})] {}".format(origin, port, binascii.hexlify(data)))
    msg = data.decode().rstrip("\x00")

    if msg[0] == "%":
        percentHandler(msg.strip("%").split("%"), origin, persistent_data)
        return

    try:
        parser = ElementTree.XMLParser(encoding="utf-8")
        elem = ElementTree.fromstring(msg, parser=parser)
        if elem.tag == "msg" and elem.attrib["t"] == "sys":
            body = elem[0]
            sysHandler(origin, body)
        elif elem.tag == "msg" and elem.attrib["xt"] == "sys":
            # ignore these for now, probably use something like xthandler
            pass
        else:
            # print(origin, "Unknown tag detected:")
            # printElem(elem)
            pass
    except Exception as e:
        # can't parse too long or too short tags correctly, need to change to a stream
        # print(e)
        # print("[{}({})] {}".format(origin, port, msg))
        pass


def percentHandler(msg, origin, persistent_data):
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
            except Exception as e:
                # print(msg[2:])
                print(e)
            pass
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
            pass
        elif msg[1] == "resultsDone":
            # game start
            pass
        elif msg[1] == "TetrisLive":
            # also a results done
            pass
        elif msg[1] == "topOut":
            # player got topped out
            pass
        else:
            print(origin, end="")
            print(msg[1:])
    else:
        print("Unknown % packet", msg)


def sysHandler(origin, body):
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
        #     f"== UserCountChange - Room: {room}, Users: {users}, Spectators: {spectators} =="
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
    else:
        print(origin, end="")
        printElem(body)


def printElem(elem, depth=0):
    print(
        "".join(" " * depth),
        "<" + elem.tag + ">",
        "attrib:",
        elem.attrib,
        "text:",
        elem.text,
    )
    for child in elem:
        printElem(child, depth=depth + 1)
