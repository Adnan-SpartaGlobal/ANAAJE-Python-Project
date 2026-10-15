"""alerts.py - post an alert when something is wrong. Stretch tier.

Real alerting posts a message to a webhook: a URL belonging to Slack, Teams or
an on-call system. fleet/webhook_receiver.py is a local stand-in for one, on
port 8805. Nothing leaves your machine.

The URL comes from the HEALTHCHECK_WEBHOOK_URL environment variable, never from
targets.yaml. targets.yaml is on GitHub. A real webhook URL in it is a secret
published to the internet, and anyone who finds it can post into your team's
channel. Treat the local URL as if it were a secret, because the habit is what
matters.

YOU WRITE THIS. The signatures are fixed.
"""

from __future__ import annotations

from checks import CheckResult

ENV_VAR = "HEALTHCHECK_WEBHOOK_URL"


def build_message(results: list[CheckResult]) -> str:
    """Build the alert text: a headline, then one line per problem.

    The headline should say the overall state and the counts. Each following
    line names the target, the check and the detail. An alert that only says
    "something is wrong" makes the reader go and look. One that names what and
    why lets them decide whether to get out of bed.
    """
    # TODO
    raise NotImplementedError("build_message() in alerts.py is not written yet")


def send_alert(results: list[CheckResult], timeout: float = 5.0) -> bool:
    """POST {"text": build_message(results)} to the webhook. Return True if sent.

    Read the URL with os.environ.get(ENV_VAR). If it is not set, log that and
    return False - not having alerting configured is not an error.

    Only alert when something is wrong. An alert on every healthy run trains
    people to ignore alerts.

    Never raise. If the webhook is down, log it and carry on. A failed alert
    must not crash the tool that found the problem, or you lose the finding as
    well as the alert.

    Never log the URL itself. Logs get pasted into tickets and chat.
    """
    # TODO
    raise NotImplementedError("send_alert() in alerts.py is not written yet")
