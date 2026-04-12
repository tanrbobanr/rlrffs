import struct
import functools
from typing import TypeVar, Iterable, Iterator


_T = TypeVar("T")


def reverse_32(i: int) -> int:
    """Reverse the byte-order of the input integer (32-bit)."""
    return struct.unpack("<I", struct.pack(">I", i))[0]


def gen_crc_table() -> list[list[int]]:
    """Generate the slice-by-16 CRC table."""
    table: list[list[int]] = [
        [None for _ in range(256)] for _ in range(16)
    ]  # 16x256 RxC

    # first row
    for col in range(256):
        crc = col << 24
        for _ in range(8):
            crc = (
                ((crc << 1) ^ 0x04C1_1DB7)
                if (crc & 0x8000_0000) > 0
                else (crc << 1)
            )

        # using mod to emulate u32 overflow behavior
        table[0][col] = reverse_32(crc % (1 << 32))

    # remaining rows
    for col in range(256):
        crc = reverse_32(table[0][col])
        for row in range(1, 16):
            crc = (reverse_32(table[0][crc >> 24]) ^ (crc << 8)) % (1 << 32)
            table[row][col] = reverse_32(crc)

    return table


CRC_TABLE = gen_crc_table()


def group_chunks(data: Iterable[_T], size: int) -> Iterator[Iterable[_T]]:
    """Groups the values within `iterable` into groups (lists) of size
    `group_size`.

    """
    clamped_size = len(data) // size * size
    return (data[n : n + size] for n in range(0, clamped_size, size))


def calc_crc(data: bytes) -> int:
    def reducer_1(acc: int, sl: bytes) -> int:
        top = int.from_bytes(sl, "little")
        one = top ^ acc
        return (
            CRC_TABLE[0][sl[15]]
            ^ CRC_TABLE[1][sl[14]]
            ^ CRC_TABLE[2][sl[13]]
            ^ CRC_TABLE[3][sl[12]]
            ^ CRC_TABLE[4][sl[11]]
            ^ CRC_TABLE[5][sl[10]]
            ^ CRC_TABLE[6][sl[9]]
            ^ CRC_TABLE[7][sl[8]]
            ^ CRC_TABLE[8][sl[7]]
            ^ CRC_TABLE[9][sl[6]]
            ^ CRC_TABLE[10][sl[5]]
            ^ CRC_TABLE[11][sl[4]]
            ^ CRC_TABLE[12][(one >> 24) & 0xFF]
            ^ CRC_TABLE[13][(one >> 16) & 0xFF]
            ^ CRC_TABLE[14][(one >> 8) & 0xFF]
            ^ CRC_TABLE[15][one & 0xFF]
        )

    crc = functools.reduce(reducer_1, group_chunks(data, 16), 0xFE0D_3410)

    leftover = len(data) % 16

    def reducer_2(acc: int, b: bytes) -> int:
        return (acc >> 8) ^ CRC_TABLE[0][b ^ (acc & 0xFF)]

    crc = functools.reduce(reducer_2, data[len(data) - leftover :], crc)

    return reverse_32((1 << 32) - crc - 1)


class CRCMismatch(Exception):
    __slots__ = ("section", "true_crc", "given_crc")

    def __init__(self, section: str, true_crc: int, given_crc: int) -> None:
        self.section = section
        self.true_crc = true_crc
        self.given_crc = given_crc

    def __str__(self) -> str:
        return (
            "The cyclic redundancy check for the given section has failed"
            f" (section={self.section}, true_crc={self.true_crc},"
            f" given_crc={self.given_crc})."
        )


def check_crc(data: bytes, crc: int) -> None:
    true_crc = calc_crc(data)
    if crc != true_crc:
        raise ValueError(f"CRC mismatch (expected {crc:x}, got {true_crc:x})")
