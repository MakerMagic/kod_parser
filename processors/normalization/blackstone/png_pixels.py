"""Lossless 8-bit RGB/RGBA PNG operations, without a Pillow ABI dependency."""

import struct
import zlib


def decode_png(data):
    width, height, depth, color, compression, filtering, interlace = struct.unpack(
        ">IIBBBBB", data[16:29]
    )
    if depth != 8 or color not in (2, 6) or compression or filtering or interlace:
        raise ValueError("Unsupported PNG format; raw asset retained")
    channels = 3 if color == 2 else 4
    if not 0 < width * height * channels <= 100_000_000:
        raise ValueError("Unsafe PNG dimensions")
    compressed, offset = bytearray(), 8
    while offset + 12 <= len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        if data[offset + 4 : offset + 8] == b"IDAT":
            compressed.extend(data[offset + 8 : offset + 8 + length])
        offset += length + 12
    stride = width * channels
    inflater = zlib.decompressobj()
    try:
        filtered = inflater.decompress(compressed, (stride + 1) * height + 1)
    except zlib.error as error:
        raise ValueError("Invalid PNG compressed pixel stream") from error
    if len(filtered) != (stride + 1) * height or not inflater.eof:
        raise ValueError("PNG pixel stream length mismatch")
    rows, previous = [], bytearray(stride)
    for y in range(height):
        method = filtered[y * (stride + 1)]
        row = bytearray(filtered[y * (stride + 1) + 1 : (y + 1) * (stride + 1)])
        if method not in range(5):
            raise ValueError("Invalid PNG row filter")
        if method:
            for i in range(stride):
                left = row[i - channels] if i >= channels else 0
                up = previous[i]
                corner = previous[i - channels] if i >= channels else 0
                if method == 1:
                    predictor = left
                elif method == 2:
                    predictor = up
                elif method == 3:
                    predictor = (left + up) // 2
                else:
                    p = left + up - corner
                    differences = (abs(p - left), abs(p - up), abs(p - corner))
                    predictor = (left, up, corner)[differences.index(min(differences))]
                row[i] = (row[i] + predictor) & 255
        rows.append(row)
        previous = row
    return width, height, channels, rows


def encode_png(width, height, channels, rows):
    def chunk(kind, payload):
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(
            b"IHDR",
            struct.pack(
                ">IIBBBBB", width, height, 8, 2 if channels == 3 else 6, 0, 0, 0
            ),
        )
        + chunk(b"IDAT", zlib.compress(b"".join(b"\x00" + row for row in rows)))
        + chunk(b"IEND", b"")
    )
