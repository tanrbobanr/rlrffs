import os
import json
import sys
sys.path.append(".")

from implementation.stream import Reader
from implementation.replay import Replay


def main() -> None:
    skip: bool = True
    skip: bool = False
    start = "P3_Soccar Strike.replay"
    directory = "replays"
    gamemodes = set()

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

    #     for frame in r.body:
    #         for event in frame.events:
    #             if isinstance(event, UpdatedActor):
    #                 for attribute in event.attributes:
    #                     if attribute.object_id == target_oid:
    #                         gamemodes.add(attribute.value)
    #                         if not seen:
    #                             print(attribute.value)
    #                             seen = True
    # print(gamemodes)

if __name__ == "__main__":
    main()
