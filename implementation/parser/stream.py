from __future__ import annotations

import os
import abc
import math
import functools
import operator
import struct
import itertools
import dataclasses
from typing import (
    TypeVar,
    TypeAlias,
    ParamSpec,
    Any,
    Self,
    overload,
    dataclass_transform,
    Callable,
    Generator,
    NoReturn,
    Sequence,
)


__all__ = (
    "Reader",
    "Writer",
)


# --- GLOBALS ----------------------------------------------------------

MAX_ASCII_LEN = 256
REVERSE_TRANS: tuple[int, ...] = tuple(
    functools.reduce(
        operator.or_, {1 << i for i in range(8) if byte & 128 >> i} or {0}
    )
    for byte in range(256)
)


# --- TYPES ------------------------------------------------------------

FileDescriptorOrPath: TypeAlias = int | str | bytes | os.PathLike
_C = TypeVar("_C", bound="ComponentBase | PrimitiveComponent")
_T = TypeVar("_T")
_P = ParamSpec("_P")
JSON: TypeAlias = (
    None | bool | int | float | str | tuple["JSON", ...] | dict[str, "JSON"]
)


# --- MISCELLANEOUS ----------------------------------------------------

def _to_signed(n: int, k: int) -> int:
    """Return the signed version of integer `n` of size `k` (bits) using
    two's-complement.

    """
    sign_bit = 1 << (k - 1)
    return (n ^ sign_bit) - sign_bit

def _to_unsigned(n: int, k: int) -> int:
    return n & ((1 << k) - 1)


def _value_to_json(value: Any) -> JSON:
    if isinstance(value, ComponentBase):
        return value.to_json()

    if value is None or isinstance(value, (int, float, str)):
        return value

    if isinstance(value, (list, tuple)):
        return tuple(_value_to_json(subvalue) for subvalue in value)

    if isinstance(value, dict):
        return {str(k):_value_to_json(v) for k, v in value.items()}

    if isinstance(value, PrimitiveComponent):
        return value.to_json()

    raise ValueError(
        "Cannot convert the following value into something that is"
        f" JSON-serializable: {value!r}"
    )


# --- READERS ----------------------------------------------------------

class Reader:
    def __init__(self, buf: bytes | memoryview) -> None:
        self._byte_buf = memoryview(buf)
        self._byte_buf_size = len(buf)
        self._byte_pos: int = 0
        self._bit_buf: int = 0
        self._bit_buf_size: int = 0

    def _read_bytes(self, count: int) -> memoryview:
        pos = self._byte_pos
        data = self._byte_buf[pos:pos + count]
        self._byte_pos += count
        self._byte_buf_size -= count
        return data

    def _eof_err(self, count: int) -> NoReturn:
        raise EOFError(
            f"Attempted to read {count} byte(s), only"
            f" {self._byte_buf_size} available in buffer"
        )

    def _refill_to(self, required_bits: int) -> None:
        required_new_bits = required_bits - self._bit_buf_size
        required_new_bytes = math.ceil(required_new_bits / 8)

        if required_new_bytes > self._byte_buf_size:
            self._eof_err(required_new_bytes)

        if required_new_bytes < 16:
            required_new_bytes = min(16, self._byte_buf_size)

        self._bit_buf |= int.from_bytes(
            self._read_bytes(required_new_bytes),
            byteorder="little"
        ) << self._bit_buf_size
        self._bit_buf_size += required_new_bytes * 8

    def _int_from_buf(self, count: int, signed: bool) -> int:
        """Take an integer from the byte buffer
        
        .. warning::
            This method assumes that the bit buffer is empty
        """
        if count > self._byte_buf_size:
            self._eof_err(count)

        pos = self._byte_pos
        data = self._byte_buf[pos:pos + count]
        self._byte_pos += count
        self._byte_buf_size -= count
        return int.from_bytes(data, "little", signed=signed)

    def __len__(self) -> int:
        return len(self._byte_buf) * 8

    @classmethod
    def from_file(cls, file: FileDescriptorOrPath) -> Self:
        with open(file, "rb") as infile:
            return cls(memoryview(infile.read()))

    def tell(self) -> int:
        """Get the current position in the stream"""
        return self._byte_pos * 8 - self._bit_buf_size

    def seek(self, target: int, whence: int = os.SEEK_SET) -> None:
        """Seek to the given target in the stream"""
        if whence == os.SEEK_SET:
            assert target >= 0
            byte_pos, bit_count = divmod(target, 8)
        elif whence == os.SEEK_CUR:
            byte_pos, bit_count = divmod(self.tell() + target, 8)
        elif whence == os.SEEK_END:
            byte_pos, bit_count = divmod(len(self) + target, 8)

        self._byte_pos = byte_pos
        self._byte_buf_size = len(self._byte_buf) - byte_pos
        self._bit_buf = 0
        self._bit_buf_size = 0
        if bit_count:
            self._refill_to(8)
            self._bit_buf >>= bit_count
            self._bit_buf_size -= bit_count

    def bits(self, count: int) -> int:
        """Take a number of bits from the bit stream, accumulated into
        an integer.

        """
        if count > self._bit_buf_size:
            self._refill_to(count)

        mask = (1 << count) - 1
        bits = self._bit_buf & mask
        self._bit_buf >>= count
        self._bit_buf_size -= count
        return bits

    def str(self) -> str:
        length = self.i32()
        return self.bytes(length)[:-1].decode("utf-8")

    def text(self) -> str:
        size = self.i32()

        if size == 0:
            return ""

        if size > 0:  # windows-1252
            return self.bytes(size)[:-1].decode("cp1252")

        # utf-16
        return self.bytes(size * -2)[:-2].decode("utf-16")

    def ascii(self) -> str:
        def gen() -> Generator[int, None, None]:
            for _ in range(MAX_ASCII_LEN):
                value = self.u8()
                if not value:
                    return
                yield value

        return bytes(gen()).decode("ascii")

    @overload
    def sized_array_of(
        self, element: type[_C], /, *args: Any, **kwargs: Any
    ) -> list[_C]: ...
    @overload
    def sized_array_of(
        self, element: Callable[_P, _T], /, *args: _P.args,
        **kwargs: _P.kwargs
    ) -> list[_T]: ...
    def sized_array_of(
        self, element: type[_C] | Callable[_P, _T], /, *args: Any,
        **kwargs: Any
    ) -> list[_C | _T]:
        size = self.u32()

        try:
            is_component = issubclass(
                element, (ComponentBase, PrimitiveComponent)
            )
        except TypeError:
            is_component = False

        if is_component:
            return [
                element.deserialize(self, *args, **kwargs)
                for _ in itertools.repeat(None, size)
            ]

        return [element(*args, **kwargs) for _ in itertools.repeat(None, size)]

    def array_of(
        self, component: type[_C], stop: Callable[[_C], bool], /, *args: Any,
        **kwargs: Any
    ) -> list[_C]:
        values: list[_C] = list()
        while True:
            value = component.deserialize(self, *args, **kwargs)
            if stop(value):
                return values
            values.append(value)

    def bytes(self, count: int) -> bytes:
        """Take a number of 8-bit sections from the bit stream,
        accumulated into a bytes object.

        """
        if count < 1:
            raise ValueError("'count' must be at least 1")

        # byte-aligned
        if not self._bit_buf_size:
            pos = self._byte_pos
            data = self._byte_buf[pos:pos + count]

            if len(data) != count:
                self._eof_err(count)

            self._byte_pos += count
            self._byte_buf_size -= count
            return bytes(data)

        return bytes(self.bits(8) for _ in itertools.repeat(None, count))

    def peek_bytes(self, count: int) -> bytes:
        if self._bit_buf_size:
            raise ValueError("You can only peek bytes when byte-aligned")
        return bytes(self._byte_buf[self._byte_pos:self._byte_pos + count])

    def bbrs(self, count: int, max: int) -> int:
        """Bounded bit-recycling sampler. Take `count` bits, and
        conditionally an extra bit if that extra bit cannot cause the
        value to be out of bounds (i.e. only if 
        `(bits(count) + (1 << count)) < max`).

        """
        if count <= 0:
            raise ValueError("'count' must be a positive non-zero integer")

        bits = self.bits(count)
        up = bits + (1 << count)

        if up >= max:
            return bits

        if self.bits(1):
            return up

        return bits

    def u8(self) -> int:
        """Read an unsigned 8-bit integer in LSB-first bit
        order and big-endian byte order.

        """
        if not self._bit_buf_size:
            return self._int_from_buf(1, False)
        return self.bits(8)

    def i8(self) -> int:
        """Read a signed 8-bit integer in LSB-first bit order
        and big-endian byte order.

        """
        if not self._bit_buf_size:
            return self._int_from_buf(1, True)
        return _to_signed(self.bits(8), 8)

    def u32(self) -> int:
        """Read an unsigned 32-bit integer in LSB-first bit
        order and big-endian byte order.

        """
        if not self._bit_buf_size:
            return self._int_from_buf(4, False)
        return self.bits(32)

    def i32(self) -> int:
        """Read a signed 32-bit integer in LSB-first bit order
        and big-endian byte order.

        """
        if not self._bit_buf_size:
            return self._int_from_buf(4, True)
        return _to_signed(self.bits(32), 32)

    def u64(self) -> int:
        """Read an unsigned 64-bit integer in LSB-first bit
        order and big-endian byte order.

        """
        if not self._bit_buf_size:
            return self._int_from_buf(8, False)
        return self.bits(64)

    def i64(self) -> int:
        """Read a signed 64-bit integer in LSB-first bit order
        and big-endian byte order.

        """
        if not self._bit_buf_size:
            return self._int_from_buf(8, True)
        return _to_signed(self.bits(64), 64)

    def f32(self) -> float:
        """Read a 32-bit float in LSB-first bit order and
        big-endian byte order.

        """
        return struct.unpack("<f", self.bytes(4))[0]

    def sn16(self) -> float:
        """Read 16-bits normalized to a float in the range `[-1,1]` in
        LSB-first bit order and big-endian byte order.

        """
        return self.bits(16) / 0xffff * 2 - 1

    def b1(self) -> bool:
        return not not self.bits(1)


class Writer:
    def __init__(self) -> None:
        self._byte_buf = bytearray()
        self._bit_buf: int = 0
        self._bit_buf_size: int = 0

    def _flush(self, force: bool = False) -> None:
        if self._bit_buf_size < 8 or (not force and self._bit_buf_size < 128):
            return

        byte_count, bit_count = divmod(self._bit_buf_size, 8)
        byte_count_bits = byte_count * 8
        mask = (1 << byte_count_bits) - 1
        self._byte_buf.extend(
            (self._bit_buf & mask).to_bytes(byte_count, "little")
        )
        self._bit_buf >>= byte_count_bits
        self._bit_buf_size = bit_count

    def _int_to_buf(self, value: int, count: int, signed: bool) -> None:
        """Put an integer directly into the byte buffer
        
        .. warning::
            This method assumes that the bit buffer is empty
        """
        self._byte_buf.extend(value.to_bytes(count, "little", signed=signed))

    @property
    def buffer(self) -> bytearray:
        return self._byte_buf

    def pad(self) -> None:
        self._flush(True)
        if self._bit_buf_size:
            self.bits(0, 8 - self._bit_buf_size)

    def flush(self) -> None:
        self._flush(True)

    def to_file(self, file: FileDescriptorOrPath) -> None:
        with open(file, "wb") as outfile:
            outfile.write(self._byte_buf)

    def bits(self, value: int, count: int) -> None:
        """Put a number of bits into the bit stream"""
        # self._bit_buf <<= count
        self._bit_buf |= value << self._bit_buf_size
        self._bit_buf_size += count
        self._flush()

    def str(self, value: str) -> None:
        encoded = value.encode("utf-8") + b"\0"
        length = len(encoded)
        self.i32(length)
        self.bytes(encoded)

    def text(self, value: str) -> None:
        encoded = value.encode("utf-16") + b"\0\0"
        self.i32(len(encoded) // -2)
        self.bytes(encoded)

    def ascii(self, value: str) -> None:
        self.bytes(value.encode("ascii") + b"\0")

    @overload
    def sized_array_of(
        self, value: Sequence[_C], /, *args: Any, **kwargs: Any
    ) -> None: ...
    @overload
    def sized_array_of(
        self, value: Sequence[Callable[_P, None]], /, *args: _P.args,
        **kwargs: _P.kwargs
    ) -> None: ...
    def sized_array_of(
        self, value: Sequence[_C | Callable[_P, None]], /, *args: Any,
        **kwargs: Any
    ) -> None:
        self.u32(len(value))

        for e in value:
            if isinstance(e, (ComponentBase, PrimitiveComponent)):
                e.serialize(self, *args, **kwargs)
            else:
                e(*args, **kwargs)

    def array_of(
        self, value: Sequence[_C], stop_value: Callable[[Self], None], /,
        *args: Any, **kwargs: Any
    ) -> None:
        for e in value:
            e.serialize(self, *args, **kwargs)
        stop_value(self)

    def bytes(self, value: bytes) -> None:
        """Put a number of 8-bit sections into the bit stream"""
        # byte-aligned
        if not self._bit_buf_size:
            self._byte_buf.extend(value)
        elif not self._bit_buf_size % 8:
            self._flush(True)
            self._byte_buf.extend(value)
        else:
            for byte in value:
                self.bits(byte, 8)

    def bbrs(self, value: int, count: int, max: int) -> None:
        base = 1 << count
        if value < base:
            up = value + base
            self.bits(value, count)
            if up < max:
                self.bits(0, 1)
        else:
            self.bits(value - base, count)
            self.bits(1, 1)

    def u8(self, value: int) -> None:
        """Read an unsigned 8-bit integer in LSB-first bit
        order and big-endian byte order.

        """
        if not self._bit_buf_size:
            return self._int_to_buf(value, 1, False)
        self.bits(value, 8)

    def i8(self, value: int) -> None:
        """Read a signed 8-bit integer in LSB-first bit order
        and big-endian byte order.

        """
        if not self._bit_buf_size:
            return self._int_to_buf(value, 1, True)
        self.bits(_to_unsigned(value, 8), 8)

    def u32(self, value: int) -> None:
        """Read an unsigned 32-bit integer in LSB-first bit
        order and big-endian byte order.

        """
        if not self._bit_buf_size:
            return self._int_to_buf(value, 4, False)
        self.bits(value, 32)

    def i32(self, value: int) -> None:
        """Read a signed 32-bit integer in LSB-first bit order
        and big-endian byte order.

        """
        if not self._bit_buf_size:
            return self._int_to_buf(value, 4, True)
        self.bits(_to_unsigned(value, 32), 32)

    def u64(self, value: int) -> None:
        """Read an unsigned 64-bit integer in LSB-first bit
        order and big-endian byte order.

        """
        if not self._bit_buf_size:
            return self._int_to_buf(value, 8, False)
        self.bits(value, 64)

    def i64(self, value: int) -> None:
        """Read a signed 64-bit integer in LSB-first bit order
        and big-endian byte order.

        """
        if not self._bit_buf_size:
            return self._int_to_buf(value, 8, True)
        self.bits(_to_unsigned(value, 64), 64)

    def f32(self, value: float) -> None:
        """Read a 32-bit float in LSB-first bit order and
        big-endian byte order.

        """
        self.bytes(struct.pack("<f", value))

    def sn16(self, value: float) -> None:
        """Read 16-bits normalized to a float in the range `[-1,1]` in
        LSB-first bit order and big-endian byte order.

        """
        return self.bits(16) / 0xffff * 2 - 1

    def b1(self, value: bool) -> None:
        self.bits(value, 1)


# --- COMPONENTS -------------------------------------------------------

class PrimitiveComponent:
    def __repr__(self) -> str:
        return f"{type(self).__name__}({super().__repr__(self)})"

    @classmethod
    def deserialize(cls, stream: Reader) -> Self:
        raise NotImplementedError()

    def serialize(self, stream: Writer) -> None:
        raise NotImplementedError()

    def to_json(self) -> JSON:
        return _value_to_json(self)


class ComponentBase:
    __slots__: tuple[str, ...]

    def __repr__(self) -> str:
        values = ", ".join(
            f"{f}={getattr(self, f)!r}" for f in self.__slots__
        )
        return f"{type(self).__name__}({values})"

    def to_json(self) -> dict[str, JSON]:
        return {k:_value_to_json(getattr(self, k)) for k in self.__slots__}

    @classmethod
    def deserialize(
        cls, stream: Reader, *args: Any, **kwargs: Any
    ) -> Self:
        raise NotImplementedError()

    def serialize(
        self, stream: Writer, *args: Any, **kwargs: Any
    ) -> None:
        raise NotImplementedError()


@dataclass_transform(kw_only_default=True, eq_default=False)
def component(cls: type[_T]) -> type[_T]:
    return dataclasses.dataclass(
        cls, repr=False, eq=False, kw_only=True, slots=True
    )
