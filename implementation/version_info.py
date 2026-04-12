from typing import NamedTuple


class NetworkVersionInfo(NamedTuple):
    num_frames: int | None
    is_rl_223: bool
    is_lan: bool
    actor_id_max: int
    actor_id_count: int
    parse_new_actor_name: bool

    @classmethod
    def build(cls, header)