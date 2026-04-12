import sys
import math
import pathlib
import statistics

sys.path.append(".")

from src.pyreplay.stream import Reader
from src.pyreplay.replay import Replay
from src.pyreplay.enums import AttributeType
from src.pyreplay.body import UpdatedActor


def main() -> None:
    replays_p = pathlib.Path(input("Replays directory: "))

    attr_percentages: dict[AttributeType, list[float]] = {
        a:list() for a in AttributeType.__members__.values()
    }
    max_attr_name_len = max(
        len(n) for n in AttributeType._member_names_
    )

    for path in replays_p.iterdir():
        print(f"Processing: {path}")

        total_attrs: int = 0
        attr_counts: dict[AttributeType, int] = {
            a:0 for a in AttributeType.__members__.values()
        }

        stream = Reader.from_file(path)
        rp = Replay.deserialize(stream)

        for frame in rp.body:
            for event in frame.events:
                if not isinstance(event, UpdatedActor):
                    continue

                for attr in event.attributes:
                    attr_counts[attr.type] += 1
                    total_attrs += 1

        for tp, count in attr_counts.items():
            attr_percentages[tp].append(count / (total_attrs or 1))

    print("Final averages:")

    means_and_errs = {
        tp:(
            statistics.mean(counts),
            statistics.stdev(counts) / math.sqrt(len(counts)),
        )
        for tp, counts in attr_percentages.items()
    }

    for tp, (mean, sterr) in sorted(
        means_and_errs.items(), key=lambda x: x[1][0], reverse=True
    ):
        p = f"{mean * 100:.8f}"
        print(
            f"    - {tp.name: <{max_attr_name_len + 1}}:"
            f" % {p: >11} +/- {sterr * 100:.8f}"
        )


if __name__ == "__main__":
    main()
