from typing import NamedTuple, Self, Iterable, Sequence

from .class_hierarchy import CLASS_INFO
from .footer import CacheEntry, Class
from .header import Header, Properties, Version


_NORMALS = (
    "TheWorld:PersistentLevel.BreakOutActor_Platform_TA",
    "TheWorld:PersistentLevel.CrowdActor_TA",
    "TheWorld:PersistentLevel.CrowdManager_TA",
    "TheWorld:PersistentLevel.InMapScoreboard_TA",
    "TheWorld:PersistentLevel.VehiclePickup_Boost_TA",
    "TheWorld:PersistentLevel.HauntedBallTrapTrigger_TA",
    "TheWorld:PersistentLevel.PlayerStart_Platform_TA",
    "TheWorld:PersistentLevel.GoalVolume_TA",
    "Archetypes.Teams.TeamWhite",
    "Archetypes.Teams.Team",
)


def normalize_object(object_name: str) -> str:
    for normal in _NORMALS:
        if normal in object_name:
            return normal
    return object_name


class CacheInfo(NamedTuple):
    stream_id_max: int
    stream_id_count: int
    object_id: int
    attributes: dict[int, int]


class PreparedCache(dict[int, CacheInfo]):
    @classmethod
    def build(
        cls, class_net_cache: Iterable[CacheEntry], classes: Iterable[Class]
    ) -> Self:
        comp_cache = cls()
        oid_to_cname = {c.object_id:c.class_name for c in classes}
        cname_to_oid = {c.class_name:c.object_id for c in classes}

        # iterate through the raw cnc
        for entry in class_net_cache:
            # build base attributes from entry
            attributes: dict[int, int] = {
                p.stream_id:p.object_id for p in entry.properties
            }

            # if not attributes:
            #     continue

            # update attributes with parent's attributes
            class_name = oid_to_cname[entry.object_id]
            parent = CLASS_INFO.get(class_name).parent

            while parent:
                oid = cname_to_oid.get(parent.name)
                info = None if oid is None else comp_cache.get(oid, None)
                if info:
                    attributes = {**info.attributes, **attributes}
                    break
                parent = parent.parent

            # get some other basic info
            stream_id_max = (max(attributes.keys()) if attributes else 2) + 1
            stream_id_count = stream_id_max.bit_length() - 1

            # create CacheInfo instance and add to comp_cnc
            info = CacheInfo(
                stream_id_max, stream_id_count, entry.object_id, attributes
            )
            comp_cache[entry.object_id] = info

        return comp_cache


class NetworkVersionInfo(NamedTuple):
    use_text_gameserver: bool
    parse_new_actor_name: bool
    simple_quats: bool

    @classmethod
    def build(cls, header: Header) -> Self:
        version = header.version

        num_frames: int | None = None
        build_version: str | None = None
        match_type: str | None = None
        max_channels: int | None = None

        for prop in header.properties:
            match prop.name:
                case "NumFrames":
                    num_frames = prop.value
                case "BuildVersion":
                    build_version = prop.value
                case "MatchType":
                    match_type = prop.value
                case "MaxChannels":
                    max_channels = prop.value

        is_lan = match_type == "Lan"

        use_text_gameserver = (
            build_version is not None
            and build_version >= "221120.42953.406184"
        )
        parse_new_actor_name = (
            version >= (868, 20)
            or (not is_lan and version >= (868, 14))
            or (is_lan and version == (868, 17))
        )
        simple_quats = version.net < 7
        large_vectors = version.net >= 7
        camset_has_transition = version >= (868, 20, 0)
        product_uses_new_color = version >= (868, 23, 8)
        product_uses_new_paint = version >= (868, 18, 0)
        product_uses_team_edition = version >= (868, 18, 0)
        large_game_mode = version >= (868, 12, 0)
        psynet_artifact = version.net < 10
        large_ps_artifact = version.net >= 1




class NetworkInfo(NamedTuple):
    num_frames: int | None
    is_rl_223: bool
    is_lan: bool
    actor_id_max: int
    actor_id_count: int
    parse_new_actor_name: bool
    cache: PreparedCache
    version: Version
    objects: Sequence[str]
    objects_inv: dict[str, int]
    normalized_objects: Sequence[str]

    @classmethod
    def build(
        cls, header_properties: Properties, version: Version,
        objects: Sequence[str], class_net_cache: Iterable[CacheEntry],
        classes: Iterable[Class]
    ) -> Self:
        # get header properties
        num_frames: int | None = None
        build_version: str | None = None
        match_type: str | None = None
        max_channels: int | None = None

        for prop in header_properties:
            match prop.name:
                case "NumFrames":
                    num_frames = prop.value
                case "BuildVersion":
                    build_version = prop.value
                case "MatchType":
                    match_type = prop.value
                case "MaxChannels":
                    max_channels = prop.value

        # determine if version is 2.23
        is_rl_223 = (
            build_version is not None
            and build_version >= "221120.42953.406184"
        )

        # determine if match type is lan
        is_lan = (
            match_type is not None
            and match_type == "Lan"
        )

        # actor ID info and such
        max_channels = 1023 if max_channels is None else max_channels

        actor_id_max = max_channels
        actor_id_count = max(0, max_channels.bit_length() - 1)
        parse_new_actor_name = (
            version >= (868, 20)
            or (not is_lan and version >= (868, 14))
            or (is_lan and version == (868, 17))
        )

        cache = PreparedCache.build(class_net_cache, classes)

        return cls(
            num_frames=num_frames,
            is_rl_223=is_rl_223,
            is_lan=is_lan,
            actor_id_max=actor_id_max,
            actor_id_count=actor_id_count,
            parse_new_actor_name=parse_new_actor_name,
            cache=cache,
            version=version,
            objects=objects,
            objects_inv={o:i for i, o in enumerate(objects)},
            normalized_objects=tuple(normalize_object(o) for o in objects)
        )
