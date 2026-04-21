from __future__ import annotations

from typing import Self

from .crc import check_crc
from .stream import Reader, ComponentBase, component, PrimitiveComponent


__all__ = (
    "ByteProperty",
    "Header",
    "KeyFrame",
    "Properties",
    "Property",
    "StructProperty",
    "Version",
)


@component
class Version(ComponentBase):
    """Represents the engine version, licensee version, net version, and
    version ID of a replay.

    """
    engine: int
    licensee: int
    net: int

    @classmethod
    def deserialize(cls, stream: Reader) -> Self:
        engine = stream.u32()
        licensee = stream.u32()

        if engine >= 866 and licensee >= 18:
            net = stream.u32()
        else:
            net = 0

        return cls(
            engine=engine,
            licensee=licensee,
            net=net
        )

    @property
    def _tup(self) -> tuple[int, int, int]:
        return (self.engine, self.licensee, self.net)

    def __lt__(self, other: tuple[int, ...]) -> bool:
        return self._tup < other

    def __le__(self, other: tuple[int, ...]) -> bool:
        return self._tup <= other

    def __gt__(self, other: tuple[int, ...]) -> bool:
        return self._tup > other

    def __ge__(self, other: tuple[int, ...]) -> bool:
        return self._tup >= other

    def __eq__(self, other: tuple[int, ...]) -> bool:
        return self._tup[:len(other)] == other

    def __ne__(self, other: tuple[int, ...]) -> bool:
        return not self.__eq__(other)


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
class ByteProperty(ComponentBase):
    key: str
    value: str | int | None

    @classmethod
    def deserialize(cls, stream: Reader, standard: bool) -> Self:
        if not standard:
            return cls(
                key=stream.text(),
                value=None
            )

        key = stream.str()

        if key == "None":
            value = stream.u8()
        else:
            value = stream.str()

        return cls(
            key=key,
            value=value
        )


@component
class StructProperty(ComponentBase):
    name: str
    fields: Properties

    @classmethod
    def deserialize(cls, stream: Reader, standard: bool) -> Self:
        return cls(
            name=stream.str(),
            fields=Properties.deserialize(stream, standard)
        )


@component
class Property(ComponentBase):
    name: str
    type: str
    unsafe_size: int
    unknown_01: tuple[int, ...]
    value: (
        int | str | float | ByteProperty | StructProperty
        | list[Properties]
    )

    @classmethod
    def deserialize(cls, stream: Reader, standard: bool) -> Self | None:
        name = stream.str()

        if name == "None":
            return

        tp = stream.str()

        unsafe_size = stream.u32()
        unknown_01 = tuple(stream.u8() for _ in range(4))

        if tp == "IntProperty":
            value = stream.i32()
        elif tp in {"StrProperty", "NameProperty"}:
            value = stream.text()
        elif tp == "FloatProperty":
            value = stream.f32()
        elif tp == "ArrayProperty":
            value = stream.sized_array_of(Properties, standard)
        elif tp == "ByteProperty":
            value = ByteProperty.deserialize(stream, standard)
        elif tp == "QWordProperty":
            value = stream.u64()
        elif tp == "BoolProperty":
            value = stream.u8() if standard else stream.u32()
        elif tp == "StructProperty":
            value = StructProperty.deserialize(stream, standard)
        else:
            raise ValueError(f"Unknown property type: {tp}")

        return cls(
            name=name,
            type=tp,
            unsafe_size=unsafe_size,
            unknown_01=unknown_01,
            value=value
        )


class Properties(list[Property], PrimitiveComponent):
    @classmethod
    def deserialize(cls, stream: Reader, standard: bool) -> Self:
        return cls(stream.array_of(
            Property, lambda p: p is None, standard
        ))


@component
class Header(ComponentBase):
    header_length: int
    header_crc: int
    version: Version
    game_type: str
    properties: Properties

    @classmethod
    def deserialize(cls, stream: Reader) -> Self:
        # whether or not the stream is buffered
        header_length = stream.u32()
        header_crc = stream.u32()

        # check header crc
        check_crc(stream.peek_bytes(header_length), header_crc)

        # read header items until we reach next CRC section
        version = Version.deserialize(stream)
        game_type = stream.text()
        properties = Properties.deserialize(stream, version != (0, 0, 0))

        return cls(
            header_length=header_length,
            header_crc=header_crc,
            version=version,
            game_type=game_type,
            properties=properties
        )
