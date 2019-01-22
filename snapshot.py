"""Decode Tetris Friends Snapshot objects."""

import base64
import zlib

FIELD_HEIGHT = 20
FIELD_WIDTH = 10


def decode_snapshot(snapshot):
    """Decode a TF snapshot object into a multidimensional list.

    :param snapshot: Snapshot in string form. This is base64 encoded and compressed with
                     zlib.
    :returns:        The decoded matrix in list form. Each row is a list of colors for
                     that cell.

    """
    buffer = zlib.decompress(base64.b64decode(snapshot))
    # print(f"buffer size: {len(buffer)}")
    incoming_lines = buffer[0]
    # print(f"{incoming_lines} incoming lines")
    pos = 1  # position in the buffer
    field = []
    for row in range(FIELD_HEIGHT):
        field_row = []
        for col in range(FIELD_WIDTH):
            byte = buffer[pos]
            mino_id = byte >> 4
            flags = byte & 0xF
            # special case for hurry up lines I think
            # print(f"SetMino mino: {mino_id}, flags: {flags}, x: {col}, y: {row}")
            if mino_id > 8:
                mino_id = 8  # use normal garbage mino for hurry up
            field_row.append(mino_id)
            pos += 1
        field.append(field_row)
    # print(field)
    # print("remaining buffer", len(buffer[pos:]), buffer[pos:])
    # comment = "{:d} lines incoming".format(incoming_lines)
    return field


if __name__ == "__main__":
    print(
        decode_snapshot(
            "eNpjWEABYGiAAQQLjQdmJmUUVRYISTAwBCprOJYIAxkMoarOPkIyQAZDiIoLAxgkZTLAQCqclc"
            "IwwgAA1cc+0w=="
        )
    )
    print(decode_snapshot("eNpjWEABaAACBhDRYGRhZMHg7MEQwJCclcHA4MIABCkMo4B0AACjLi2N"))
    print(
        decode_snapshot("eNpjWEABaAACBhDRYGRhZMHg7FEYwJCclcHA4FJUV8GQwjAKSAcA6gEvZg==")
    )
