from __future__ import annotations

from typing import *

from .stream import Reader, ComponentBase, component, PrimitiveComponent
from .network_info import NetworkInfo
from .attributes import Vec3i, Rotation, Attribute, Pointer
from .enums import SpawnTrajectory
from .class_hierarchy import CLASS_INFO


@component
class DeletedActor(ComponentBase):
    event_id: int
    frame_id: int
    actor_id: int


@component
class CreatedActor(ComponentBase):
    event_id: int
    frame_id: int
    actor_id: int
    name_id: int | None
    type_id: Pointer
    initial_location: Vec3i | None
    initial_rotation: Rotation | None

    @classmethod
    def deserialize(
        cls, stream: Reader, network_info: NetworkInfo, event_id: int,
        frame_id: int, actor_id: int
    ) -> Self:
        if network_info.parse_new_actor_name:
            name_id = stream.i32()
        else:
            name_id = None

        type_id = Pointer.deserialize(stream)
        norm_type = network_info.normalized_objects[type_id.target_id]
        type_info = CLASS_INFO[norm_type]

        # spawn trajectory
        trajectory = type_info.spawn_trajectory
        if trajectory is SpawnTrajectory.none:
            initial_location = None
            initial_rotation = None
        else:
            # either loc or loc_rot, so we always deserialize location
            initial_location = Vec3i.deserialize(stream, network_info)

            if trajectory is SpawnTrajectory.loc_rot:
                initial_rotation = Rotation.deserialize(stream)
            else:
                initial_rotation = None

        return cls(
            event_id=event_id,
            frame_id=frame_id,
            actor_id=actor_id,
            name_id=name_id,
            type_id=type_id,
            initial_location=initial_location,
            initial_rotation=initial_rotation
        )


@component
class UpdatedActor(ComponentBase):
    event_id: int
    frame_id: int
    actor_id: int
    object_id: int
    attributes: tuple[Attribute, ...]

    @classmethod
    def deserialize(
        cls, stream: Reader, network_info: NetworkInfo, event_id: int,
        frame_id: int, actor_id: int, active_actors: dict[int, int]
    ) -> Self:
        object_id = active_actors[actor_id]
        nobj = network_info.normalized_objects[object_id]
        obj_info = CLASS_INFO[nobj]

        cache_info = network_info.cache.get(object_id)

        # augment prepped_cache if cache info is missing
        if cache_info is None:
            if obj_info.parent is None:
                raise ValueError(
                    "Attempted to update prepared cache with an object that"
                    f" has no parent: {obj_info!r}"
                )

            parent_object_id = network_info.objects_inv[obj_info.parent.name]
            cache_info = network_info.cache[parent_object_id]
            network_info.cache[object_id] = cache_info

        # get stream id info from cache info
        sid_max = cache_info.stream_id_max
        sid_count = cache_info.stream_id_count

        attributes: list[Attribute] = list()

        # iteratively parse new attributes while the next bit is on
        while stream.bits(1):
            stream_id = stream.bbrs(sid_count, sid_max)

            # get attribute object
            attr_obj = cache_info.attributes[stream_id]

            # parse attribute
            attributes.append(Attribute.deserialize(
                stream, network_info, stream_id, attr_obj
            ))

        return cls(
            event_id=event_id,
            frame_id=frame_id,
            actor_id=actor_id,
            object_id=object_id,
            attributes=tuple(attributes)
        )


@component
class Frame(ComponentBase):
    frame_id: int
    time: float
    delta: float
    events: tuple[CreatedActor | UpdatedActor | DeletedActor, ...]

    @classmethod
    def deserialize(
        cls, stream: Reader, network_info: NetworkInfo, frame_id: int,
        active_actors: dict[int, int]
    ) -> Self:
        time = stream.f32()
        delta = stream.f32()
        if time < 0 or 0 < time < 1e-10 or delta < 0 or 0 < delta < 1e-10:
            raise ValueError(
                f"Time or delta is out of range: time={time} delta={delta}"
            )

        events: list[CreatedActor | UpdatedActor | DeletedActor] = list()
        event_id = -1
        aid_count = network_info.actor_id_count
        aid_max = network_info.actor_id_max

        # actors
        while stream.bits(1):  # frame contains more actor data
            actor_id = stream.bbrs(aid_count, aid_max)
            event_id += 1

            if stream.bits(1):  # actor is alive (i.e. new or updated)
                if stream.bits(1):  # actor is new
                    event = CreatedActor.deserialize(
                        stream, network_info, event_id, frame_id, actor_id
                    )
                    events.append(event)
                    active_actors[actor_id] = event.type_id.target_id
                else:  # actor is updated
                    events.append(UpdatedActor.deserialize(
                        stream,
                        network_info,
                        event_id,
                        frame_id,
                        actor_id,
                        active_actors
                    ))

            else:  # actor has been deleted
                events.append(DeletedActor(
                    event_id=event_id,
                    frame_id=frame_id,
                    actor_id=actor_id
                ))
                if actor_id in active_actors:
                    del active_actors[actor_id]

        return cls(
            frame_id=frame_id,
            time=time,
            delta=delta,
            events=tuple(events)
        )


class Body(list[Frame], PrimitiveComponent):
    pad_bytes: bytes
    pad_bits: int
    pad_bit_count: int

    @classmethod
    def deserialize(
        cls, stream: Reader, network_info: NetworkInfo, body_length: int
    ) -> Self:
        body = cls()
        body.pad_bits = 0

        if network_info.num_frames is None:
            body.pad_bytes = bytes()
            body.pad_bit_count = 0
            return body

        body_start_pos = stream.tell()
        body_stop_pos = body_start_pos + body_length * 8

        active_actors: dict[int, int] = dict()

        for frame_id in range(network_info.num_frames):
            body.append(Frame.deserialize(
                stream, network_info, frame_id, active_actors
            ))

        # get padding
        # NOTE: only required for reproducing a replay file in a fully
        # lossless manner (not just no loss of information, but exact
        # replication of structure). The padding is likely to never be
        # anything other than a bunch of zeros, but since we don't have
        # the official specification, we can't say for sure
        current_pos = stream.tell()
        body.pad_bit_count = pad_bit_count = (8 - current_pos % 8) % 8
        if pad_bit_count:
            body.pad_bits = stream.bits(pad_bit_count)
            current_pos += pad_bit_count

        num_extra_bytes = (body_stop_pos - current_pos) // 8
        if num_extra_bytes:
            body.pad_bytes = stream.bytes(num_extra_bytes)
        else:
            body.pad_bytes = bytes()

        return body
