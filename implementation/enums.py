import enum


class SpawnTrajectory(enum.Enum):
    none = enum.auto()
    loc = enum.auto()
    loc_rot = enum.auto()


class TileState(enum.IntEnum):
    undamaged = 0
    damaged = 1
    destroyed = 2


# class Playlist(enum.Enum):
#     SpeedDemon = 38
#     Knockout = 54
#     Private = 6


class AttributeType(enum.Enum):
    actor_base = enum.auto()
    applied_damage = enum.auto()
    boolean = enum.auto()
    camera_settings = enum.auto()
    club_colors = enum.auto()
    damage_state = enum.auto()
    demolish = enum.auto()
    demolish_extended = enum.auto()
    demolish_fx = enum.auto()
    explosion = enum.auto()
    explosion_extended = enum.auto()
    float_32 = enum.auto()
    game_mode = enum.auto()
    game_server = enum.auto()
    guid = enum.auto()
    impulse = enum.auto()
    int_32 = enum.auto()
    int_64 = enum.auto()
    loadout = enum.auto()
    loadout_online = enum.auto()
    loadouts_online = enum.auto()
    logo_data = enum.auto()
    match_settings = enum.auto()
    music_stinger = enum.auto()
    new_pickup = enum.auto()
    party_leader = enum.auto()
    pickup = enum.auto()
    pickup_info = enum.auto()
    player_history_key = enum.auto()
    rep_stat_title = enum.auto()
    replicated_boost = enum.auto()
    reservation = enum.auto()
    rigid_body = enum.auto()
    rotation = enum.auto()
    skill_tier = enum.auto()
    string = enum.auto()
    pointer = enum.auto()
    team_loadouts = enum.auto()
    team_paint = enum.auto()
    title = enum.auto()
    uint_11 = enum.auto()
    uint_8 = enum.auto()
    unique_id = enum.auto()
    vector_3f = enum.auto()
    vector_3i = enum.auto()
    welded_info = enum.auto()


class ProductValue(enum.IntEnum):
    no_color = 0
    old_color = 1
    new_color = 2
    old_paint = 3
    new_paint = 4
    title = 5
    special_edition = 6
    old_team_edition = 7
    new_team_edition = 8


class Platform(enum.IntEnum):
    split_screen = 0
    steam = 1
    playstation = 2
    xbox = 4
    qq = 5
    switch = 6
    psynet = 7
    epic = 11
