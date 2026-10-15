"""Shared vocabulary for every check. This file is complete - read it, do not rewrite it.

Your team will write three or four check modules at the same time, on separate
branches. If each person invented their own way of reporting a result, the
afternoon would be spent gluing four different shapes together. So the shape is
agreed here, before anyone starts: every check returns a CheckResult.

Three states, and the difference between them is the heart of the project:

  OK        the check passed
  DEGRADED  we reached the target and it told us something is wrong
  DOWN      we could not reach the target at all

DEGRADED and DOWN are different findings that need different responses. A
service returning HTTP 500 needs someone to read its logs. A service refusing
connections needs someone to find out whether the host is even alive. Reporting
both as "failed" throws away the most useful thing your check learned.

Use it like this:

    from checks import OK, DOWN, CheckResult

    return CheckResult(target="fleet-node-01", check="tcp", state=OK,
                       detail="connected to 127.0.0.1:8801", latency_ms=1.2)
"""

from dataclasses import dataclass, field

OK = "OK"
DEGRADED = "DEGRADED"
DOWN = "DOWN"

# Ordered worst first, for deciding the overall exit code.
STATES = (DOWN, DEGRADED, OK)


@dataclass
class CheckResult:
    """One check against one target.

    target      the target's name from targets.yaml
    check       which check produced this: "tcp", "http", "disk" or "ping"
    state       OK, DEGRADED or DOWN
    detail      one line a human can act on, such as "HTTP 500: database down"
    latency_ms  how long the check took, if that means anything for this check
    extra       anything else worth keeping. The HTTP check puts the parsed
                /health body in extra["payload"] so the disk check can read it.
    """

    target: str
    check: str
    state: str
    detail: str
    latency_ms: float | None = None
    extra: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.state == OK

    def as_dict(self) -> dict:
        """Plain dictionary, for the JSON report."""
        return {
            "target": self.target,
            "check": self.check,
            "state": self.state,
            "detail": self.detail,
            "latency_ms": self.latency_ms,
            **self.extra,
        }
