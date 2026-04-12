import sys
import math
import pathlib
import statistics

sys.path.append(".")

from src.pyreplay.stream import Reader
from src.pyreplay.header import Header
from src.pyreplay.metadata import Metadata


def main() -> None:
    replays_p = pathlib.Path(input("Replays directory: "))

    header_sizes: list[float] = list()
    metadata_sizes: list[float] = list()
    body_sizes: list[float] = list()
    footer_sizes: list[float] = list()

    for path in replays_p.iterdir():
        print(f"Processing: {path}")

        stream = Reader.from_file(path)
        hdr = Header.deserialize(stream)
        mta = Metadata.deserialize(stream)

        t_size = len(stream) // 8
        h_size = hdr.header_length + 8
        m_size = mta.metadata_length
        b_size = mta.body_length
        f_size = t_size - h_size - m_size - b_size

        header_sizes.append(h_size / t_size)
        metadata_sizes.append(m_size / t_size)
        body_sizes.append(b_size / t_size)
        footer_sizes.append(f_size / t_size)

        print(f"    h={h_size} m={m_size} b={b_size} f={f_size} t={t_size}")

    print("Final averages:")

    for name, sizes in (
        ("Header", header_sizes),
        ("Metadata", metadata_sizes),
        ("Body", body_sizes),
        ("Footer", footer_sizes),
    ):
        mean = statistics.mean(sizes)
        stdev = statistics.stdev(sizes)
        sterr = stdev / math.sqrt(len(sizes))

        p = f"{mean * 100:.8f}"
        print(f"    - {name: <9}: % {p: >11} +/- {sterr * 100:.8f}")


if __name__ == "__main__":
    main()
