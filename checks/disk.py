"""checks/disk.py - is the disk filling up? Extension tier.

Two functions, and the difference between them is the lesson.

Your tool runs on YOUR machine. shutil.disk_usage() reads the disk of the
machine running the code that calls it - yours. It cannot read a fleet node's
disk, however you call it.

So the fleet nodes do what real services do: each one measures its own disk and
reports the figure in its /health response. Open fleet/node_ok.py and look at
the "disk" block. Your tool reads the number from there.

YOU WRITE THIS. The signatures and contracts are fixed.
"""

from __future__ import annotations

from pathlib import Path
import shutil

from . import DEGRADED, OK, CheckResult

CHECK_NAME = "disk"


def check_reported_disk(name: str, payload: dict, threshold_percent: int) -> CheckResult:
    """Compare a target's self-reported disk usage against the threshold.

    payload is the parsed /health body that the HTTP check already fetched.
    Read payload["disk"]["percent_used"].

      percent_used below the threshold        ->  OK
      percent_used at or above the threshold  ->  DEGRADED
      no disk figures in the payload, or not a number  ->  DEGRADED, and say so

    The threshold comes from targets.yaml, never from a number in this file.
    Thresholds are configuration: you tune an alert by editing a config file,
    not by changing code and redeploying.

    Try it: lower disk_threshold_percent in targets.yaml to 40 and run again.
    The same honest reading from node 01 now crosses the line.
    """
    # TODO
    try:
        percent_used = payload["disk"]["percent_used"]
    except (KeyError, TypeError):
        return DEGRADED("No valid disk usage data found in payload")

    if percent_used < threshold_percent:
        return CheckResult(target=name, check=CHECK_NAME, state=OK, detail=f"Disk usage is {percent_used}% which is below the threshold of {threshold_percent}%")
    else:
        return CheckResult(target=name, check=CHECK_NAME, state=DEGRADED, detail=f"Disk usage is {percent_used}% which is at or above the threshold of {threshold_percent}%")


def check_local_disk(threshold_percent: int, path: Path | None = None) -> CheckResult:
    """Check the disk of the machine this tool is running on.

    Use shutil.disk_usage(path), defaulting path to the current directory. Work
    out percent used from the .used and .total it gives you.

    Label the result honestly: the target is this machine, not a fleet node.
    That is still worth checking. When the machine running your monitoring
    fills up, the thing that would have warned you is the thing that broke.

    Same states as above: DEGRADED at or above the threshold, OK below it.
    """
    # TODO
    usage = shutil.disk_usage(path or Path.cwd())
    percent_used = (usage.used / usage.total) * 100

    if percent_used < threshold_percent:
        return CheckResult(target="local", check=CHECK_NAME, state=OK, detail=f"Local disk usage is {percent_used}% which is below the threshold of {threshold_percent}%")
    else:
        return CheckResult(target="local", check=CHECK_NAME, state=DEGRADED, detail=f"Local disk usage is {percent_used}% which is at or above the threshold of {threshold_percent}%")
