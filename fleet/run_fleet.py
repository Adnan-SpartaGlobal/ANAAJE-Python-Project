"""fleet/run_fleet.py - start the whole fake fleet in one command.

    python fleet/run_fleet.py

That starts three servers as child processes and leaves them running until you
press Ctrl+C. Port 8804 is NOT started, and that is the point - your tool has to
cope with a target that is not there.

Add --webhook to also start the alert receiver on 8805. You need that only for
the stretch tier.

This script uses subprocess to start and stop other programs. You will write
code like it yourself in the stretch tier when you shell out to ping, so it is
worth reading once you get there.
"""

import argparse
import logging
import subprocess
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s [run_fleet] %(message)s",
)
log = logging.getLogger("run_fleet")

# The directory this script lives in, so the fleet starts from anywhere.
# Path(__file__).resolve().parent is the reliable way to say "next to me".
# Relative paths like "fleet/node_ok.py" only work if you happen to be standing
# in the right directory, and you will not always be.
FLEET_DIR = Path(__file__).resolve().parent

NODES = [
    ("node_ok.py", 8801, "healthy"),
    ("node_broken.py", 8802, "up, but /health returns 500"),
    ("node_slow.py", 8803, "up, but /health takes 10 seconds"),
]

WEBHOOK_NODE = ("webhook_receiver.py", 8805, "alert receiver, stretch tier only")

# Nothing is started on this port. Deliberately.
MISSING_PORT = 8804


def start(script_name, port, description):
    """Start one node as a child process and return it."""
    script = FLEET_DIR / script_name
    log.info("starting %-20s on port %d  (%s)", script_name, port, description)
    return subprocess.Popen([sys.executable, str(script)])


def main():
    parser = argparse.ArgumentParser(description="Start the fake fleet.")
    parser.add_argument(
        "--webhook",
        action="store_true",
        help="also start the alert receiver on port 8805 (stretch tier)",
    )
    args = parser.parse_args()

    to_start = list(NODES)
    if args.webhook:
        to_start.append(WEBHOOK_NODE)

    processes = [start(*node) for node in to_start]

    log.warning("nothing is listening on port %d - that is deliberate, and your "
                "tool must handle it", MISSING_PORT)
    log.info("fleet running. Press Ctrl+C to stop it.")

    try:
        for process in processes:
            process.wait()
    except KeyboardInterrupt:
        log.info("stopping the fleet")
        for process in processes:
            process.terminate()
        for process in processes:
            process.wait()
        log.info("fleet stopped")


if __name__ == "__main__":
    main()
