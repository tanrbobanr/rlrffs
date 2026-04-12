from __future__ import annotations

from typing import Self

from .crc import check_crc
from .stream import Reader, ComponentBase, component


@component
class KeyFrame(ComponentBase):
    """A keyframe"""
    time: float
    frame: int
    file_position: int

    @classmethod
    def deserialize(cls, stream: Reader) -> Self:
        return cls(
            time=stream.f32(),
            frame=stream.u32(),
            file_position=stream.u32()
        )


@component
class Metadata(ComponentBase):
    metadata_length: int # synthesized
    eof_length: int
    eof_crc: int
    levels: tuple[str, ...]
    keyframes: tuple[KeyFrame, ...]
    body_length: int

    @classmethod
    def deserialize(cls, stream: Reader) -> Self:
        start = stream.tell()

        eof_length = stream.u32()
        eof_crc = stream.u32()

        # check eof crc
        check_crc(stream.peek_bytes(eof_length), eof_crc)

        levels = stream.sized_array_of(stream.text)
        keyframes = stream.sized_array_of(KeyFrame)
        body_length = stream.u32()

        return cls(
            metadata_length=(stream.tell() - start) // 8,
            eof_length=eof_length,
            eof_crc=eof_crc,
            levels=levels,
            keyframes=keyframes,
            body_length=body_length
        )
