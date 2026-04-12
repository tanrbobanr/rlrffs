from __future__ import annotations

import os
from typing import Self

from .stream import Reader, ComponentBase, component
from .network_info import NetworkInfo
from .header import Header
from .metadata import Metadata
from .footer import Footer
from .body import Body


__all__ = (
    "Replay",
    "ReplayFraming",
)


@component
class ReplayFraming(ComponentBase):
    header: Header
    metadata: Metadata
    footer: Footer
    network_info: NetworkInfo

    @classmethod
    def deserialize(cls, stream: Reader) -> Self:
        # header and metadata
        header = Header.deserialize(stream)
        metadata = Metadata.deserialize(stream)

        # skip body
        stream.seek(metadata.body_length * 8, os.SEEK_CUR)

        # footer
        footer = Footer.deserialize(stream)

        network_info = NetworkInfo.build(
            header.properties,
            header.version,
            footer.objects,
            footer.class_net_cache,
            footer.classes
        )

        return cls(
            header=header,
            metadata=metadata,
            footer=footer,
            network_info=network_info
        )


@component
class Replay(ComponentBase):
    header: Header
    metadata: Metadata
    body: Body
    footer: Footer
    network_info: NetworkInfo

    @classmethod
    def deserialize(cls, stream: Reader) -> Self:
        # header and metadata
        header = Header.deserialize(stream)
        metadata = Metadata.deserialize(stream)

        # skip body
        stream.seek(metadata.body_length * 8, os.SEEK_CUR)

        # footer
        footer = Footer.deserialize(stream)

        # body
        network_info = NetworkInfo.build(
            header.properties,
            header.version,
            footer.objects,
            footer.class_net_cache,
            footer.classes
        )

        # add 8 because `header_length` does not include u32 for
        # `header_length` and u32 for `header_crc`
        stream.seek(
            (header.header_length + metadata.metadata_length + 8) * 8,
            os.SEEK_SET
        )
        body = Body.deserialize(stream, network_info, metadata.body_length)

        return cls(
            header=header,
            metadata=metadata,
            body=body,
            footer=footer,
            network_info=network_info
        )
