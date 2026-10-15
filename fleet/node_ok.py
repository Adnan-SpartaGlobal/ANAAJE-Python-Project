"""fleet/node_ok.py - a healthy server, for you to check against.

This is one of the four fake servers that make up your fleet. You do not edit
these files. You check them.

This one is the baseline: it is up, it is well, and it answers quickly. When
your tool says something is wrong with this node, the bug is in your tool.

Start it on its own with:

    python fleet/node_ok.py

Or start the whole fleet at once with:

    python fleet/run_fleet.py
"""

import logging

from flask import Flask, jsonify

PORT = 8801
NODE_NAME = "fleet-node-01"

# A real service reports its own disk figures, because nothing outside the
# machine can read them for it. These numbers are a fixture - they are fixed so
# that everyone in the room sees the same result - but the shape is exactly what
# a real health endpoint returns.
DISK_TOTAL_GB = 80
DISK_USED_GB = 33
DISK_PERCENT_USED = 41

logging.basicConfig(
    level=logging.INFO,
    format=f"%(asctime)s %(levelname)-8s [{NODE_NAME}] %(message)s",
)
log = logging.getLogger(NODE_NAME)

app = Flask(NODE_NAME)


@app.route("/")
def index():
    """The service doing its actual job."""
    return jsonify({"node": NODE_NAME, "message": "serving traffic"})


@app.route("/health")
def health():
    """The health endpoint your tool will check.

    Two things are worth noticing, because your own checks depend on both.

    The status code says whether the service is well: 200 means yes. Your tool
    reads that first.

    The body says *how* well, in detail a status code cannot carry. Disk
    headroom lives here because only this machine can measure its own disk.
    Your tool reads the body second and compares the figure against the
    threshold in targets.yaml.
    """
    return jsonify(
        {
            "node": NODE_NAME,
            "status": "ok",
            "version": "1.4.2",
            "disk": {
                "total_gb": DISK_TOTAL_GB,
                "used_gb": DISK_USED_GB,
                "percent_used": DISK_PERCENT_USED,
            },
        }
    )


if __name__ == "__main__":
    log.info("starting on port %d - this node is healthy", PORT)
    app.run(host="127.0.0.1", port=PORT)
