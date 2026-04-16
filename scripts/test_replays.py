import os
import json
import sys
import statistics

sys.path.append(".")

from implementation import *


def main() -> None:
    skip: bool = True
    skip: bool = False
    start = "P3_Soccar Strike.replay"
    directory = "replays"

    x_pre_7: list[float] = list()
    y_pre_7: list[float] = list()
    z_pre_7: list[float] = list()
    x_post_7: list[float] = list()
    y_post_7: list[float] = list()
    z_post_7: list[float] = list()

    for fname in os.listdir(directory):
        if not start:
            skip = False

        if skip:
            if fname == start:
                skip = False
            else:
                continue

        print(fname)

        r = Replay.deserialize(
            Reader.from_file(os.path.join(directory, fname))
        )


        # for p in r.header.properties:
        #     if p.name == "PlayerStats" and isinstance(p.value, list):
        #         for props in p.value:
        #             for p2 in props:
        #                 if p2.name == "Platform" and isinstance(p2.value, ByteProperty):
        #                     platforms.add(p2.value.value)

    #     if "ProjectX.GRI_X:ReplicatedGamePlaylist" in r.footer.objects:
    #         target_oid = r.footer.objects.index("ProjectX.GRI_X:ReplicatedGamePlaylist")
    #     else:
    #         target_oid = None

    #     seen = False


        for frame in r.body:
            for event in frame.events:
                if isinstance(event, UpdatedActor):
                    for i, attribute in enumerate(event.attributes):
                        v = attribute.value
                        if isinstance(v, (Explosion, ExplosionExtended)):
                            if isinstance(v, ExplosionExtended):
                                v = v.explosion
                            vecs = (v.location,)
                            for vec in vecs:
                                if r.header.version.net >= 7:
                                    x_post_7.append(vec.x)
                                    y_post_7.append(vec.y)
                                    z_post_7.append(vec.z)
                                else:
                                    x_pre_7.append(vec.x)
                                    y_pre_7.append(vec.y)
                                    z_pre_7.append(vec.z)

    for values, name in (
        (x_pre_7, "x_pre_7"),
        (y_pre_7, "y_pre_7"),
        (z_pre_7, "z_pre_7"),
        (x_post_7, "x_post_7"),
        (y_post_7, "y_post_7"),
        (z_post_7, "z_post_7"),
    ):
        lo = min(values)
        hi = max(values)
        mean = statistics.mean(values)
        print(f"{name: <8}  {lo}-{hi} ({mean})")


if __name__ == "__main__":
    main()
