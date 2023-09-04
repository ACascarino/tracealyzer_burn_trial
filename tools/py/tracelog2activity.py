#!/usr/bin/env python
import argparse
import csv
import pathlib
import statistics

# Returns a range showing the overlapping values between two input ranges
OVERLAP = lambda x, y: range(max(x[0], y[0]), min(x[-1], y[-1]) + 1)

# We know these are the four columns output - give them sensible names
TRACEALYZER_OUTPUT_FIELDNAMES = ("TS", "Actor", "CPU", "Event")

# The CPU ID is always the final character in this column
CPU_ID = lambda tag: int(tag[-1])

# Timestamps are always of the form (s+).mmm.uuu, so can get a whole no. of us
TS_TO_US = lambda ts: int(ts.replace(".", ""))

# When we report sliding stdev, what window size are we using?
SLIDING_STDEV_TIME = 1000000  # us, = 1s

# And what resolution are we using for reporting utilisation percentage?
ACCUMULATION_TIME = 10000  # us, = 10ms

# These become header names for the output CSV - all the info we generate
OUTPUT_STATS = (
    "Core ID",
    "Mean CPU Usage (%)",
    "Std.Dev CPU Usage (%)",
    f"Min. CPU Usage (% with {ACCUMULATION_TIME // 1000} ms window)",
    f"Max. CPU Usage (% with {ACCUMULATION_TIME // 1000} ms window)",
    f"Min. Std.Dev CPU Usage (% with {SLIDING_STDEV_TIME // 1000} ms window)",
    f"Max. Std.Dev CPU Usage (% with {SLIDING_STDEV_TIME // 1000} ms window)",
)


class Core:
    def __init__(self, id: int) -> None:
        self.id: int = id
        self.idle_times: list[int] = list()
        self.wake_times: list[int] = list()
        self.wake_ranges: list[range] = list()
        self.utilisation: dict[int, float] = dict()
        self.stdev_utilisation_sliding: dict[int, float] = dict()
        self.average_utilisation: float = 0.0
        self.min_utilisation: float = 0.0
        self.max_utilisation: float = 0.0
        self.stdev_utilisation: float = 0.0
        self.min_sliding_stdev: float = 0.0
        self.max_sliding_stdev: float = 0.0

    def __repr__(self) -> str:
        return f"core[{self.id}]"

    def calculate_wake_ranges(self) -> None:
        """Populates self.wake_ranges with all ranges where Core is not idle"""
        current_time = 0
        for ts in self.wake_times:
            # We want to ignore multiple wake times with no idle times between
            if ts > current_time:
                next_idle_time = self.get_next_idle_time_after(ts)
                self.wake_ranges.append(range(ts, next_idle_time))
                current_time = next_idle_time

    def calculate_utilisation_in_windows(self, windows: list[range]) -> None:
        """Populates self.utilisation with % non-idle per window"""
        # This really isn't very efficient but it doesn't need to be
        for idx, window in enumerate(windows):
            overlapping_microseconds = 0
            # Get applicable wake ranges
            for awake in self.wake_ranges:
                overlapping_microseconds += len(OVERLAP(awake, window))
            self.utilisation |= {idx: overlapping_microseconds / len(window)}

    def calculate_sliding_stdev_utilisation(self, hop):
        """Populates self.stdev_utilisation_sliding with coarse stddev info"""
        ix = [range(i, i + hop) for i in range(len(self.utilisation) - hop + 1)]
        for idx, coarse_range in enumerate(ix):
            values = [self.utilisation[x] for x in coarse_range]
            self.stdev_utilisation_sliding |= {idx: statistics.stdev(values)}

    def calculate_average_utilisation(self) -> float:
        """Sets self.average_utilisation to mean(self.utilisation)"""
        self.average_utilisation = statistics.mean(self.utilisation.values())
        return self.average_utilisation

    def calculate_min_utilisation(self) -> float:
        """Sets self.min_utilisation to min(self.utilisation)"""
        self.min_utilisation = min(self.utilisation.values())
        return self.min_utilisation

    def calculate_max_utilisation(self) -> float:
        """Sets self.max_utilisation to max(self.utilisation)"""
        self.max_utilisation = max(self.utilisation.values())
        return self.max_utilisation

    def calculate_stdev_utilisation(self) -> float:
        """Sets self.stdev_utilisation to stddev of self.utilisation"""
        self.stdev_utilisation = statistics.stdev(self.utilisation.values())
        return self.stdev_utilisation

    def calculate_min_sliding_stdev(self) -> float:
        """Sets self.min_sliding_stdev to min(self.stdev_utilisation_sliding)"""
        self.min_sliding_stdev = min(self.stdev_utilisation_sliding.values())
        return self.min_sliding_stdev

    def calculate_max_sliding_stdev(self) -> float:
        """Sets self.min_sliding_stdev to max(self.stdev_utilisation_sliding)"""
        self.max_sliding_stdev = max(self.stdev_utilisation_sliding.values())
        return self.max_sliding_stdev

    def get_next_idle_time_after(self, ts) -> int:
        return min(filter(lambda i: i > ts, self.idle_times))


def parse_csv(input: pathlib.Path) -> tuple[int, int, dict[int, Core]]:
    """Convert Tracealyzer CSV to trace start and end times and init.d Cores"""
    cpus: dict[int, Core] = dict()
    rows: list[dict[str, str]] = list()  # Irritatingly, can't unpack in hint
    trace_start = 0
    trace_end = 0

    with open(input, "r") as f:
        reader = csv.DictReader(f, fieldnames=TRACEALYZER_OUTPUT_FIELDNAMES)

        for row in reader:
            cpu_idx = CPU_ID(row["CPU"]) if row["CPU"] else None
            if cpu_idx is not None and cpu_idx not in cpus.keys():
                cpus |= {cpu_idx: Core(cpu_idx)}
            rows.append(row)

    for row in rows:
        # We want all cores to start idle and finish idle
        if "Trace Start" in row["Event"]:
            trace_start = TS_TO_US(row["TS"])
            for cpu in cpus.values():
                cpu.idle_times.append(trace_start)
        elif "Trace End" in row["Event"]:
            trace_end = TS_TO_US(row["TS"])
            for cpu in cpus.values():
                cpu.idle_times.append(trace_end)
        # Otherwise, log when each core switches from/to any IDLE task
        elif "IDLE" in row["Actor"]:
            cpus[CPU_ID(row["CPU"])].idle_times.append(TS_TO_US(row["TS"]))
        else:
            cpus[CPU_ID(row["CPU"])].wake_times.append(TS_TO_US(row["TS"]))

    return (trace_start, trace_end, cpus)


def analyse_results(start: int, end: int, cpus: dict[int, Core]) -> None:
    # Generate time ranges for our subsamples
    # Extend the final window to cover to the very end
    bounds = list(range(start, end, ACCUMULATION_TIME))[:-1] + [end]
    windows = [range(x, bounds[i + 1]) for i, x in enumerate(bounds[:-1])]

    # How many accumulated utilisation percentages fit into our larger window?
    sliding_window_count = SLIDING_STDEV_TIME // ACCUMULATION_TIME

    for cpu in cpus.values():
        cpu.calculate_utilisation_in_windows(windows)
        cpu.calculate_sliding_stdev_utilisation(sliding_window_count)
        cpu.calculate_average_utilisation()
        cpu.calculate_max_utilisation()
        cpu.calculate_min_utilisation()
        cpu.calculate_stdev_utilisation()
        cpu.calculate_max_sliding_stdev()
        cpu.calculate_min_sliding_stdev()


def output_report(output: pathlib.Path, cpus: dict[int, Core]) -> None:
    with open(output, "w") as f:
        writer = csv.DictWriter(f, OUTPUT_STATS)

        writer.writeheader()
        for cpu in cpus.values():
            op_dict = dict()
            op_dict[OUTPUT_STATS[0]] = cpu.id
            op_dict[OUTPUT_STATS[1]] = cpu.average_utilisation
            op_dict[OUTPUT_STATS[2]] = cpu.stdev_utilisation
            op_dict[OUTPUT_STATS[3]] = cpu.min_utilisation
            op_dict[OUTPUT_STATS[4]] = cpu.max_utilisation
            op_dict[OUTPUT_STATS[5]] = cpu.min_sliding_stdev
            op_dict[OUTPUT_STATS[6]] = cpu.max_sliding_stdev
            writer.writerow(op_dict)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        action="store",
        type=pathlib.Path,
        required=True,
        help="Path to input CSV",
    )
    parser.add_argument(
        "-o",
        "--output",
        action="store",
        type=pathlib.Path,
        required=False,
        default="out.csv",
        help="Path to output CSV",
    )
    args = parser.parse_args()

    # Get all timing info
    trace_start, trace_end, cpus = parse_csv(args.input)
    total_exec_time_us = trace_end - trace_start

    # Parse it into active time ranges per core
    for cpu in cpus.values():
        cpu.calculate_wake_ranges()

    analyse_results(trace_start, trace_end, cpus)

    output_report(args.output, cpus)
