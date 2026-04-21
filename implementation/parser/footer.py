from __future__ import annotations

from typing import Self

from .stream import Reader, ComponentBase, component


__all__ = (
    "CacheEntry",
    "CacheProperty",
    "Class",
    "DebugString",
    "Footer",
    "TickMark",
)


@component
class DebugString(ComponentBase):
    frame: int
    username: str
    text: str

    @classmethod
    def deserialize(cls, stream: Reader) -> Self:
        return cls(
            frame=stream.u32(),
            username=stream.text(),
            text=stream.text()
        )


@component
class TickMark(ComponentBase):
    description: str
    frame: int

    @classmethod
    def deserialize(cls, stream: Reader) -> Self:
        return cls(
            description=stream.text(),
            frame=stream.u32()
        )


@component
class Class(ComponentBase):
    class_name: str
    object_id: int

    @classmethod
    def deserialize(cls, stream: Reader) -> Self:
        return cls(
            class_name=stream.str(),
            object_id=stream.u32()
        )


@component
class CacheProperty(ComponentBase):
    object_id: int
    stream_id: int

    @classmethod
    def deserialize(cls, stream: Reader) -> Self:
        return cls(
            object_id=stream.u32(),
            stream_id=stream.u32()
        )


@component
class CacheEntry(ComponentBase):
    object_id: int
    parent_id: int
    cache_id: int
    properties: tuple[CacheProperty, ...]

    @classmethod
    def deserialize(cls, stream: Reader) -> Self:
        return cls(
            object_id=stream.u32(),
            parent_id=stream.u32(),
            cache_id=stream.u32(),
            properties=stream.sized_array_of(CacheProperty)
        )


@component
class Footer(ComponentBase):
    debug_strings: tuple[DebugString, ...]
    tick_marks: tuple[TickMark, ...]
    packages: tuple[str, ...]
    objects: tuple[str, ...]
    names: tuple[str, ...]
    classes: tuple[Class, ...]
    class_net_cache: tuple[CacheEntry, ...]

    @classmethod
    def deserialize(cls, stream: Reader) -> Self:
        return cls(
            debug_strings=stream.sized_array_of(DebugString),
            tick_marks=stream.sized_array_of(TickMark),
            packages=stream.sized_array_of(stream.text),
            objects=stream.sized_array_of(stream.text),
            names=stream.sized_array_of(stream.text),
            classes=stream.sized_array_of(Class),
            class_net_cache=stream.sized_array_of(CacheEntry)
        )
