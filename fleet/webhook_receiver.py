"""fleet/webhook_receiver.py - somewhere for your alerts to go.

You need this only for the stretch tier.

Real alerting posts to a webhook: a URL belonging to Slack, Teams, PagerDuty or
whatever the team uses. This is a local stand-in for one. It accepts a POST,
prints the JSON body it received, and returns 200. Nothing leaves your machine.

Start it alongside the fleet, then point your tool at it:

    export HEALTHCHECK_WEBHOOK_URL=http://127.0.0.1:8805/webhook

On Windows PowerShell:

    $env:HEALTHCHECK_WEBHOOK_URL = "http://127.0.0.1:8805/webhook"

Notice where that URL lives. It is an environment variable, not a line in
targets.yaml. That is the habit the stretch tier is really teaching: a real
webhook URL is a secret, your repository is on GitHub, and anyone holding the
URL can post into your team's channel. Config goes in the config file. Secrets
go in the environment.
"""

import logging

from flask import Flask, jsonify, request

PORT = 8805
NODE_NAME = "webhook-receiver"

logging.basicConfig(
    level=logging.INFO,
    format=f"%(asctime)s %(levelname)-8s [{NODE_NAME}] %(message)s",
)
log = logging.getLogger(NODE_NAME)

app = Flask(NODE_NAME)


@app.route("/webhook", methods=["POST"])
def webhook():
    """Accept an alert and show it.

    `silent=True` means a body that is not valid JSON gives None rather than
    raising. A receiver that crashes on a malformed alert is worse than one
    that logs it, because you lose the alert *and* the receiver.
    """
    payload = request.get_json(silent=True)
    if payload is None:
        log.warning("received a POST whose body was not valid JSON")
        return jsonify({"received": False, "reason": "body was not valid JSON"}), 400

    log.info("alert received: %s", payload)
    return jsonify({"received": True})


if __name__ == "__main__":
    log.info("starting on port %d - POST your alerts to /webhook", PORT)
    app.run(host="127.0.0.1", port=PORT)
