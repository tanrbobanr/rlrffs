import math
import itertools
from typing import Self, Any, TypeAlias, NamedTuple

from .stream import Reader, ComponentBase, PrimitiveComponent, component
from .network_info import NetworkInfo
from .enums import ProductValue, Platform, AttributeType, TileState, Platform
from .class_hierarchy import CLASS_INFO


ROT_CONVERSION = 360 / 256

# 1/sqrt(2)
QUAT_MAX_QUAT = 0.70710678118654752440084436210485
# (1 << 18) - 1
QUAT_MAX_VALUE = 262_143


@component
class Pointer(ComponentBase):
    is_actor: bool
    target_id: int

    @classmethod
    def deserialize(cls, stream: Reader, *args: Any, **kwargs: Any) -> Self:
        return cls(
            is_actor=stream.b1(),
            target_id=stream.i32()
        )


@component
class Rotation(ComponentBase):
    """Represents a 3-axis rotation"""
    pitch: float | None
    yaw: float | None
    roll: float | None

    @classmethod
    def deserialize(cls, stream: Reader, *args: Any, **kwargs: Any) -> Self:
        return cls(
            pitch=stream.i8() * ROT_CONVERSION if stream.b1() else None,
            yaw=stream.i8() * ROT_CONVERSION if stream.b1() else None,
            roll=stream.i8() * ROT_CONVERSION if stream.b1() else None
        )


@component
class Quaternion(ComponentBase):
    x: float
    y: float
    z: float
    w: float

    @staticmethod
    def _unpack(val: int) -> float:
        """Convert the input unsigned integer (18 bits) to a float
        normalized to the range [-1/sqrt(2),1/sqrt(2)].

        """
        pos_rng = val / QUAT_MAX_VALUE
        rng = (pos_rng - 0.5) * 2
        return rng * QUAT_MAX_QUAT

    @classmethod
    def deserialize(cls, stream: Reader, network_info: NetworkInfo) -> Self:
        # NOTE: Probably move this into its own vector
        if network_info.version.net < 7:
            return cls(
                x=stream.sn16(),
                y=stream.sn16(),
                z=stream.sn16(),
                w=0.0
            )

        largest = stream.bits(2)

        a = cls._unpack(stream.bits(18))
        b = cls._unpack(stream.bits(18))
        c = cls._unpack(stream.bits(18))

        extra = math.sqrt(1.0 - (a * a) - (b * b) - (c * c))

        if largest == 0:
            return cls(x=extra, y=a, z=b, w=c)
        if largest == 1:
            return cls(x=a, y=extra, z=b, w=c)
        if largest == 2:
            return cls(x=a, y=b, z=extra, w=c)
        return cls(x=a, y=b, z=c, w=extra)


@component
class Vec3i(ComponentBase):
    x: int
    y: int
    z: int

    @classmethod
    def deserialize(cls, stream: Reader, network_info: NetworkInfo) -> Self:
        size_max = 22 if network_info.version.net >= 7 else 20
        size = stream.bbrs(4, size_max)
        bias = 1 << (size + 1)
        bit_limit = size + 2
        return cls(
            x=(stream.bits(bit_limit) - bias),
            y=(stream.bits(bit_limit) - bias),
            z=(stream.bits(bit_limit) - bias)
        )


@component
class Vec3f(ComponentBase):
    x: float
    y: float
    z: float

    @classmethod
    def deserialize(cls, stream: Reader, network_info: NetworkInfo) -> Self:
        size_max = 22 if network_info.version.net >= 7 else 20
        size = stream.bbrs(4, size_max)
        bias = 1 << (size + 1)
        bit_limit = size + 2
        return cls(
            x=(stream.bits(bit_limit) - bias) / 100,
            y=(stream.bits(bit_limit) - bias) / 100,
            z=(stream.bits(bit_limit) - bias) / 100
        )


@component
class AppliedDamage(ComponentBase):
    id: int
    position: Vec3f
    damage_index: int
    total_damage: int

    @classmethod
    def deserialize(cls, stream: Reader, network_info: NetworkInfo) -> Self:
        return cls(
            id=stream.u8(),
            position=Vec3f.deserialize(stream, network_info),
            damage_index=stream.i32(),
            total_damage=stream.i32()
        )


class Boolean(int, PrimitiveComponent):
    @classmethod
    def deserialize(cls, stream: Reader, *args: Any, **kwargs: Any) -> Self:
        return cls(stream.b1())

    def to_json(self) -> bool:
        return not not self


@component
class CameraSettings(ComponentBase):
    fov: float
    height: float
    angle: float
    distance: float
    stiffness: float
    swivel: float
    transition: float | None

    @classmethod
    def deserialize(cls, stream: Reader, network_info: NetworkInfo) -> Self:
        return cls(
            fov=stream.f32(),
            height=stream.f32(),
            angle=stream.f32(),
            distance=stream.f32(),
            stiffness=stream.f32(),
            swivel=stream.f32(),
            transition=(
                stream.f32()
                if network_info.version >= (868, 20, 0)
                else None
            )
        )


@component
class ClientLoadout(ComponentBase):
    version: int
    body: int
    decal: int
    wheels: int
    rocket_trail: int
    antenna: int
    topper: int
    unknown_04: int
    unknown_05: int | None
    engine_audio: int | None
    trail: int | None
    goal_explosion: int | None
    banner: int | None
    product_id: int | None
    unknown_06: int | None
    unknown_07: int | None
    unknown_08: int | None

    @classmethod
    def deserialize(cls, stream: Reader, *args: Any, **kwargs: Any) -> Self:
        version = stream.u8()

        # version 0+
        body = stream.u32()
        decal = stream.u32()
        wheels = stream.u32()
        rocket_trail = stream.u32()
        antenna = stream.u32()
        topper = stream.u32()
        unknown_04 = stream.u32()

        # version 11+
        if version >= 11:
            unknown_05 = stream.u32()
        else:
            unknown_05 = None

        # version 16+
        if version >= 16:
            engine_audio = stream.u32()
            trail = stream.u32()
            goal_explosion = stream.u32()
        else:
            engine_audio = None
            trail = None
            goal_explosion = None

        # version 17+
        if version >= 17:
            banner = stream.u32()
        else:
            banner = None

        # version 19+
        if version >= 19:
            product_id = stream.u32()
        else:
            product_id = None

        # version 22+
        if version >= 22:
            unknown_06 = stream.u32()
            unknown_07 = stream.u32()
            unknown_08 = stream.u32()
        else:
            unknown_06 = None
            unknown_07 = None
            unknown_08 = None

        return cls(
            version=version,
            body=body,
            decal=decal,
            wheels=wheels,
            rocket_trail=rocket_trail,
            antenna=antenna,
            topper=topper,
            unknown_04=unknown_04,
            unknown_05=unknown_05,
            engine_audio=engine_audio,
            trail=trail,
            goal_explosion=goal_explosion,
            banner=banner,
            product_id=product_id,
            unknown_06=unknown_06,
            unknown_07=unknown_07,
            unknown_08=unknown_08
        )


@component
class Product(ComponentBase):
    unknown_09: bool
    object_id: int
    value_type: ProductValue | None
    value: int | str | None

    @classmethod
    def deserialize(cls, stream: Reader, network_info: NetworkInfo) -> Self:
        unknown_09 = stream.b1()
        object_id = stream.u32()
        obj = network_info.objects[object_id]

        # get the value type and value of the product
        if obj == "TAGame.ProductAttribute_UserColor_TA":
            if network_info.version >= (868, 23, 8):
                value_type = ProductValue.new_color
                value = stream.u32()
            elif stream.b1():
                value_type = ProductValue.old_color
                value = stream.bits(31)
            else:
                value_type = ProductValue.no_color
                value = None
        elif obj == "TAGame.ProductAttribute_Painted_TA":
            if network_info.version >= (868, 18, 0):
                value_type = ProductValue.new_paint
                value = stream.bits(31)
            else:
                value_type = ProductValue.old_paint
                value = stream.bbrs(3, 14)
        elif obj == "TAGame.ProductAttribute_SpecialEdition_TA":
            value_type = ProductValue.special_edition
            value = stream.bits(31)
        elif obj == "TAGame.ProductAttribute_TeamEdition_TA":
            if network_info.version >= (868, 18, 0):
                value_type = ProductValue.new_team_edition
                value = stream.bits(31)
            else:
                value_type = ProductValue.old_team_edition
                raise ValueError("found it!")
                value = stream.bbrs(3, 14)
        elif obj == "TAGame.ProductAttribute_TitleID_TA":
            value_type = ProductValue.title
            value = stream.text()
        else:
            value_type = value = None

        return cls(
            unknown_09=unknown_09,
            object_id=object_id,
            value_type=value_type,
            value=value
        )


class ClientLoadoutOnline(list[list[Product]], PrimitiveComponent):
    @classmethod
    def deserialize(cls, stream: Reader, network_info: NetworkInfo) -> Self:
        return cls(
            [
                Product.deserialize(stream, network_info)
                for _ in range(stream.u8())
            ]
            for _ in range(stream.u8())
        )


@component
class TeamLoadouts(ComponentBase):
    blue: ClientLoadout
    orange: ClientLoadout

    @classmethod
    def deserialize(cls, stream: Reader, *args: Any, **kwargs: Any) -> Self:
        return cls(
            blue=ClientLoadout.deserialize(stream),
            orange=ClientLoadout.deserialize(stream)
        )


@component
class ClientLoadoutsOnline(ComponentBase):
    blue: ClientLoadoutOnline | None
    orange: ClientLoadoutOnline | None
    unknown_10: bool
    unknown_11: bool

    @classmethod
    def deserialize(cls, stream: Reader, network_info: NetworkInfo) -> Self:
        return cls(
            blue=ClientLoadoutOnline.deserialize(stream, network_info),
            orange=ClientLoadoutOnline.deserialize(stream, network_info),
            unknown_10=stream.b1(),
            unknown_11=stream.b1()
        )


@component
class ClubColors(ComponentBase):
    blue_flag: bool
    blue_color: int
    orange_flag: bool
    orange_color: int

    @classmethod
    def deserialize(cls, stream: Reader, *args: Any, **kwargs: Any) -> Self:
        return cls(
            blue_flag=stream.b1(),
            blue_color=stream.u8(),
            orange_flag=stream.b1(),
            orange_color=stream.u8()
        )


@component
class DamageState(ComponentBase):
    tile_state: TileState
    damaged: bool
    offender: int
    ball_position: Vec3f
    direct_hit: bool
    immediate: bool

    @classmethod
    def deserialize(cls, stream: Reader, network_info: NetworkInfo) -> Self:
        return cls(
            tile_state=TileState(stream.u8()),
            damaged=stream.b1(),
            offender=stream.i32(),
            ball_position=Vec3f.deserialize(stream, network_info),
            direct_hit=stream.b1(),
            immediate=stream.b1()
        )


@component
class Demolish(ComponentBase):
    attacker: Pointer
    victim: Pointer
    attack_velocity: Vec3f
    victim_velocity: Vec3f

    @classmethod
    def deserialize(cls, stream: Reader, network_info: NetworkInfo) -> Self:
        return cls(
            attacker=Pointer.deserialize(stream),
            victim=Pointer.deserialize(stream),
            attack_velocity=Vec3f.deserialize(stream, network_info),
            victim_velocity=Vec3f.deserialize(stream, network_info)
        )


@component
class DemolishFx(ComponentBase):
    custom_demo_fx: Pointer
    demolish: Demolish

    @classmethod
    def deserialize(cls, stream: Reader, network_info: NetworkInfo) -> Self:
        return cls(
            custom_demo_fx=Pointer.deserialize(stream),
            demolish=Demolish.deserialize(stream, network_info)
        )


@component
class DemolishExtended(ComponentBase):
    attacker_pri: Pointer
    self_demo_fx: Pointer
    self_demo: bool
    goal_explosation_owner: Pointer
    demolish: Demolish

    @classmethod
    def deserialize(cls, stream: Reader, network_info: NetworkInfo) -> Self:
        return cls(
            attacker_pri=Pointer.deserialize(stream),
            self_demo_fx=Pointer.deserialize(stream),
            self_demo=stream.b1(),
            goal_explosation_owner=Pointer.deserialize(stream),
            demolish=Demolish.deserialize(stream, network_info)
        )


@component
class Explosion(ComponentBase):
    goal: Pointer
    location: Vec3f

    @classmethod
    def deserialize(cls, stream: Reader, network_info: NetworkInfo) -> Self:
        return cls(
            goal=Pointer.deserialize(stream),
            location=Vec3f.deserialize(stream, network_info)
        )


@component
class ExplosionExtended(ComponentBase):
    explosion: Explosion
    scorer: Pointer

    @classmethod
    def deserialize(cls, stream: Reader, network_info: NetworkInfo) -> Self:
        return cls(
            explosion=Explosion.deserialize(stream, network_info),
            scorer=Pointer.deserialize(stream)
        )


class Float32(float, PrimitiveComponent):
    @classmethod
    def deserialize(cls, stream: Reader, *args: Any, **kwargs: Any) -> Self:
        return cls(stream.f32())


class GameMode(int, PrimitiveComponent):
    @classmethod
    def deserialize(cls, stream: Reader, network_info: NetworkInfo) -> Self:
        return cls(stream.bits(
            2 if network_info.version < (868, 12, 0) else 8
        ))


@component
class GameServer(ComponentBase):
    value: str | int

    @classmethod
    def deserialize(cls, stream: Reader, network_info: NetworkInfo) -> Self:
        if network_info.is_rl_223:
            return cls(value=stream.text())
        return cls(value=stream.u64())

    def to_json(self) -> str | int:
        return self.value


@component
class Impulse(ComponentBase):
    compressed_rotation: int
    speed: float

    @classmethod
    def deserialize(cls, stream: Reader, *args: Any, **kwargs: Any) -> Self:
        return cls(
            compressed_rotation=stream.i32(),
            speed=stream.f32()
        )


class Int32(int, PrimitiveComponent):
    @classmethod
    def deserialize(cls, stream: Reader, *args: Any, **kwargs: Any) -> Self:
        return cls(stream.i32())


@component
class LogoData(ComponentBase):
    swap_colors: bool
    logo_id: int

    @classmethod
    def deserialize(cls, stream: Reader, *args: Any, **kwargs: Any) -> Self:
        return cls(
            swap_colors=stream.b1(),
            logo_id=stream.u32()
        )


@component
class MusicStinger(ComponentBase):
    flag: bool
    cue: int
    trigger: int

    @classmethod
    def deserialize(cls, stream: Reader, *args: Any, **kwargs: Any) -> Self:
        return cls(
            flag=stream.b1(),
            cue=stream.u32(),
            trigger=stream.u8()
        )


@component
class NewPickupData(ComponentBase):
    instigator: int | None
    picked_up: int

    @classmethod
    def deserialize(cls, stream: Reader, *args: Any, **kwargs: Any) -> Self:
        return cls(
            instigator=stream.i32() if stream.b1() else None,
            picked_up=stream.u8()
        )


@component
class PsyNetRemoteID(ComponentBase):
    online_id: int
    unknown_29: list[int] | None

    @classmethod
    def deserialize(cls, stream: Reader, network_info: NetworkInfo) -> Self:
        return cls(
            online_id=stream.u64(),
            unknown_29=(
                list(stream.bytes(24))
                if network_info.version.net < 10
                else None
            )
        )


@component
class SwitchRemoteID(ComponentBase):
    online_id: int
    unknown_30: list[int]

    @classmethod
    def deserialize(cls, stream: Reader, *args: Any, **kwargs: Any) -> Self:
        return cls(
            online_id=stream.u64(),
            unknown_30=list(stream.bytes(24))
        )


@component
class PSNRemoteID(ComponentBase):
    name: str
    shard: str
    region: str
    platform: str
    unknown_31: list[int]
    online_id: int | None

    @classmethod
    def deserialize(cls, stream: Reader, network_info: NetworkInfo) -> Self:
        return cls(
            name=stream.bytes(16).strip(b"\0").decode("cp1252"),
            shard=stream.bytes(2).decode("cp1252"),
            region=stream.bytes(2).decode("cp1252"),
            platform=stream.bytes(4).strip(b"\0").decode("cp1252"),
            unknown_31=list(stream.bytes(8)),
            online_id=(stream.u64() if network_info.version.net >= 1 else None)
        )


@component
class SplitScreenRemoteID(ComponentBase):
    online_id: int

    @classmethod
    def deserialize(cls, stream: Reader, *args: Any, **kwargs: Any) -> Self:
        return cls(online_id=stream.bits(24))


@component
class EpicRemoteID(ComponentBase):
    online_id: str

    @classmethod
    def deserialize(cls, stream: Reader, *args: Any, **kwargs: Any) -> Self:
        return cls(online_id=stream.text())


@component
class U64RemoteID(ComponentBase):
    online_id: int

    @classmethod
    def deserialize(cls, stream: Reader, *args: Any, **kwargs: Any) -> Self:
        return cls(online_id=stream.u64())


RemoteID: TypeAlias = (
    PsyNetRemoteID
    | SwitchRemoteID
    | PSNRemoteID
    | SplitScreenRemoteID
    | EpicRemoteID
    | U64RemoteID
)


PlatformMap: dict[Platform, type[RemoteID]] = {
    Platform.split_screen: SplitScreenRemoteID,
    Platform.steam: U64RemoteID,
    Platform.playstation: PSNRemoteID,
    Platform.xbox: U64RemoteID,
    Platform.qq: U64RemoteID,
    Platform.switch: SwitchRemoteID,
    Platform.psynet: PsyNetRemoteID,
    Platform.epic: EpicRemoteID,
}


@component
class UniqueID(ComponentBase):
    platform: Platform
    remote_id: RemoteID
    local_id: int

    @classmethod
    def deserialize(
        cls, stream: Reader, network_info: NetworkInfo,
        platform: int | None = None
    ) -> Self:
        platform = Platform(
            platform if platform is not None else stream.u8()
        )
        remote_id = PlatformMap[platform].deserialize(stream, network_info)

        return cls(
            platform=platform,
            remote_id=remote_id,
            local_id=stream.u8()
        )


@component
class PartyLeader(ComponentBase):
    unique_id: UniqueID | None

    @classmethod
    def deserialize(cls, stream: Reader, network_info: NetworkInfo) -> Self:
        system_id = stream.u8()
        if system_id == 0:
            return cls(unique_id=None)
        return cls(unique_id=UniqueID.deserialize(
            stream, network_info, system_id
        ))


@component
class PickupData(ComponentBase):
    instigator: int | None
    picked_up: bool

    @classmethod
    def deserialize(cls, stream: Reader, *args: Any, **kwargs: Any) -> Self:
        return cls(
            instigator=stream.i32() if stream.b1() else None,
            picked_up=stream.b1()
        )


@component
class PickupInfo(ComponentBase):
    available_pickups: list[Pointer] # the three available tactical rumble options
    items_are_preview: bool

    @classmethod
    def deserialize(cls, stream: Reader, *args: Any, **kwargs: Any) -> Self:
        return cls(
            available_pickups=[
                Pointer.deserialize(stream),
                Pointer.deserialize(stream),
                Pointer.deserialize(stream),
            ],
            items_are_preview=stream.b1()
        )


class PlayerHistoryKey(int, PrimitiveComponent):
    @classmethod
    def deserialize(cls, stream: Reader, *args: Any, **kwargs: Any) -> Self:
        return cls(stream.bits(14))


@component
class PrivateMatchSettings(ComponentBase):
    mutators: str
    joinable_by: int
    max_players: int
    game_name: str
    password: str
    is_public: bool

    @classmethod
    def deserialize(cls, stream: Reader, *args: Any, **kwargs: Any) -> Self:
        return cls(
            mutators=stream.text(),
            joinable_by=stream.u32(),  # or map_name?
            max_players=stream.u32(),
            game_name=stream.text(),
            password=stream.text(),
            is_public=stream.b1()
        )


@component
class RepStatTitle(ComponentBase):
    unknown_16: bool
    name: str
    unknown_17: bool
    idx: int
    value: int

    @classmethod
    def deserialize(cls, stream: Reader, *args: Any, **kwargs: Any) -> Self:
        return cls(
            unknown_16=stream.b1(),
            name=stream.text(),
            unknown_17=stream.b1(),
            idx=stream.u32(),
            value=stream.u32()
        )


@component
class Reservation(ComponentBase):
    number: int
    unique_id: UniqueID
    name: str | str | None
    unknown_18: bool
    unknown_19: bool
    unknown_20: int | None

    @classmethod
    def deserialize(cls, stream: Reader, network_info: NetworkInfo) -> Self:
        number = stream.bits(3)
        # number = 0
        unique_id = UniqueID.deserialize(stream, network_info)

        if unique_id.platform != Platform.split_screen:
            name = stream.text()
        elif unique_id.remote_id.online_id != 0:
            name = stream.ascii()
        else:
            name = None

        return cls(
            number=number,
            unique_id=unique_id,
            name=name,
            unknown_18=stream.b1(),
            unknown_19=stream.b1(),
            unknown_20=(
                stream.bits(6) if network_info.version >= (868, 12, 0)
                else None
            )
        )


@component
class RigidBody(ComponentBase):
    sleeping: bool
    location: Vec3f
    rotation: Quaternion
    linear_velocity: Vec3f | None
    angular_velocity: Vec3f | None

    @classmethod
    def deserialize(cls, stream: Reader, network_info: NetworkInfo) -> Self:
        sleeping = stream.bits(1)
        location = Vec3f.deserialize(stream, network_info)
        rotation = Quaternion.deserialize(stream, network_info)

        if sleeping:
            linear_velocity, angular_velocity = None, None
        else:
            linear_velocity = Vec3f.deserialize(stream, network_info)
            angular_velocity = Vec3f.deserialize(stream, network_info)

        return cls(
            sleeping=sleeping,
            location=location,
            rotation=rotation,
            linear_velocity=linear_velocity,
            angular_velocity=angular_velocity
        )


@component
class SkillTier(ComponentBase):
    flag: bool
    value: int

    @classmethod
    def deserialize(cls, stream: Reader, *args: Any, **kwargs: Any) -> Self:
        return cls(
            flag=stream.b1(),
            value=stream.u8()
        )


@component
class TeamPaint(ComponentBase):
    team: int
    primary_color: int
    accent_color: int
    primary_finish: int
    accent_finish: int

    @classmethod
    def deserialize(cls, stream: Reader, *args: Any, **kwargs: Any) -> Self:
        return cls(
            team=stream.u8(),
            primary_color=stream.u8(),
            accent_color=stream.u8(),
            primary_finish=stream.u32(),
            accent_finish=stream.u32()
        )


@component
class Title(ComponentBase):
    unknown_21: bool
    unknown_22: bool
    unknown_23: int
    unknown_24: int
    unknown_25: int
    unknown_26: int
    unknown_27: int
    unknown_28: bool

    @classmethod
    def deserialize(cls, stream: Reader, *args: Any, **kwargs: Any) -> Self:
        return Title(
            unknown_21=stream.bits(1),
            unknown_22=stream.bits(1),
            unknown_23=stream.u32(),
            unknown_24=stream.u32(),
            unknown_25=stream.u32(),
            unknown_26=stream.u32(),
            unknown_27=stream.u32(),
            unknown_28=stream.bits(1)
        )


class UInt8(int, PrimitiveComponent):
    @classmethod
    def deserialize(cls, stream: Reader, *args: Any, **kwargs: Any) -> Self:
        return cls(stream.u8())


class UInt11(int, PrimitiveComponent):
    @classmethod
    def deserialize(cls, stream: Reader, *args: Any, **kwargs: Any) -> Self:
        return UInt11(stream.bits(11))


class Int64(int, PrimitiveComponent):
    @classmethod
    def deserialize(cls, stream: Reader, *args: Any, **kwargs: Any) -> Self:
        return cls(stream.i64())


@component
class WeldedInfo(ComponentBase):
    active: bool
    actor_id: int
    offset: Vec3f
    mass: float
    rotation: Rotation

    @classmethod
    def deserialize(cls, stream: Reader, network_info: NetworkInfo) -> Self:
        return cls(
            active=stream.b1(),
            actor_id=stream.i32(),
            offset=Vec3f.deserialize(stream, network_info),
            mass=stream.f32(),
            rotation=Rotation.deserialize(stream)
        )


@component
class ReplicatedBoost(ComponentBase):
    grant_count: int
    boost_amount: int
    unknown_32: int
    unknown_33: int

    @classmethod
    def deserialize(cls, stream: Reader, *args: Any, **kwargs: Any) -> Self:
        return cls(
            grant_count=stream.u8(),
            boost_amount=stream.u8(),
            unknown_32=stream.u8(),
            unknown_33=stream.u8()
        )


class String16(str, PrimitiveComponent):
    @classmethod
    def deserialize(cls, stream: Reader, *args: Any, **kwargs: Any) -> Self:
        return cls(stream.text())


AttributeValueType: TypeAlias = (
    AppliedDamage
    | Boolean
    | CameraSettings
    | ClientLoadout
    | ClientLoadoutOnline
    | ClientLoadoutsOnline
    | ClubColors
    | DamageState
    | Demolish
    | DemolishFx
    | Explosion
    | ExplosionExtended
    | Float32
    | GameMode
    | GameServer
    | Impulse
    | Int32
    | Int64
    | Int64
    | LogoData
    | MusicStinger
    | NewPickupData
    | PartyLeader
    | PickupData
    | PickupInfo
    | PlayerHistoryKey
    | PrivateMatchSettings
    | ReplicatedBoost
    | RepStatTitle
    | Reservation
    | RigidBody
    | Rotation
    | SkillTier
    | String16
    | Pointer
    | TeamLoadouts
    | TeamPaint
    | Title
    | UInt11
    | UInt8
    | UniqueID
    | Vec3f
    # | Vector3i
    | WeldedInfo
)


_attribute_type_map: dict[AttributeType, AttributeValueType] = {
    # AttributeType.actor_base: ActorBase,
    AttributeType.pointer: Pointer,
    AttributeType.applied_damage: AppliedDamage,
    AttributeType.boolean: Boolean,
    AttributeType.camera_settings: CameraSettings,
    AttributeType.club_colors: ClubColors,
    AttributeType.damage_state: DamageState,
    AttributeType.demolish_extended: DemolishExtended,
    AttributeType.demolish_fx: DemolishFx,
    AttributeType.demolish: Demolish,
    AttributeType.explosion_extended: ExplosionExtended,
    AttributeType.explosion: Explosion,
    AttributeType.float_32: Float32,
    AttributeType.game_mode: GameMode,
    AttributeType.game_server: GameServer,
    AttributeType.impulse: Impulse,
    AttributeType.int_32: Int32,
    AttributeType.int_64: Int64,
    AttributeType.loadout_online: ClientLoadoutOnline,
    AttributeType.loadout: ClientLoadout,
    AttributeType.loadouts_online: ClientLoadoutsOnline,
    AttributeType.logo_data: LogoData,
    AttributeType.match_settings: PrivateMatchSettings,
    AttributeType.music_stinger: MusicStinger,
    AttributeType.new_pickup: NewPickupData,
    AttributeType.party_leader: PartyLeader,
    AttributeType.pickup_info: PickupInfo,
    AttributeType.pickup: PickupData,
    AttributeType.player_history_key: PlayerHistoryKey,
    AttributeType.rep_stat_title: RepStatTitle,
    AttributeType.replicated_boost: ReplicatedBoost,
    AttributeType.reservation: Reservation,
    AttributeType.rigid_body: RigidBody,
    AttributeType.rotation: Rotation,
    AttributeType.skill_tier: SkillTier,
    AttributeType.string: String16,
    AttributeType.team_loadouts: TeamLoadouts,
    AttributeType.team_paint: TeamPaint,
    AttributeType.title: Title,
    AttributeType.uint_11: UInt11,
    AttributeType.uint_8: UInt8,
    AttributeType.unique_id: UniqueID,
    AttributeType.vector_3f: Vec3f,
    # AttributeType.vector_3i: Vector3i,
    AttributeType.welded_info: WeldedInfo,
}


@component
class Attribute(ComponentBase):
    stream_id: int
    object_id: int
    type: AttributeType
    value: AttributeValueType

    @classmethod
    def deserialize(
        cls, stream: Reader, network_info: NetworkInfo, stream_id: int,
        object_id: int
    ) -> Self:
        object_name = network_info.objects[object_id]
        attribute_type = CLASS_INFO[object_name].attribute_type

        if attribute_type is None:
            raise ValueError(
                "Attribute attempted to deserialize a non-attribute:"
                f" {object_name!r}"
            )

        attribute_model = _attribute_type_map[attribute_type]
        return cls(
            stream_id=stream_id,
            object_id=object_id,
            type=attribute_type,
            value=attribute_model.deserialize(stream, network_info)
        )
