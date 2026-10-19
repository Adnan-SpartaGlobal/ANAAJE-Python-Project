"""checks/ping.py - an ICMP ping, run through subprocess. Stretch tier.

This is the check most people expect a health-check tool to start with. It is
in the stretch tier rather than the core for good reasons, and finding out
those reasons is part of the job:

  - The ping command takes different flags on Windows from Linux and macOS.
  - Many corporate networks block ping entirely.
  - Many containers cannot run ping without extra permissions.

If ping fails on your network but the TCP check works, that is a genuine
finding to report in your demo, not a bug to fix.

YOU WRITE THIS. The signatures and contracts are fixed.
"""

from __future__ import annotations
import platform
import subprocess
from . import DEGRADED, OK, CheckResult

CHECK_NAME = "ping"


def ping_command(host: str, count: int = 1, timeout_seconds: int = 2) -> list[str]:
    """Return the ping command for this operating system, as a list of strings.

    platform.system() tells you which operating system you are on. Find out the
    count and timeout flags for Windows and for Linux and macOS yourself - run
    `ping` with no arguments, or read its help - and notice that the timeout is
    not measured in the same unit on both.

    Return a list such as ["ping", "-c", "1", "127.0.0.1"], never one string.
    A list goes straight to the operating system with no shell in between, so a
    strange host name cannot turn into a shell command.
    """
    os_system = platform.system()

    if os_system == "Darwin" or os_system == "Linux":
        return ["ping", "-c", str(count), "-W", str(timeout_seconds), host]
    else:  # Windows
        return ["ping", "-n", str(count), "-w", str(timeout_seconds * 1000), host]


def check_ping(name: str, host: str, timeout_seconds: int = 2) -> CheckResult:
    """Run ping once with subprocess.run and report on its exit code.

    Judge by the exit code, not by the text ping prints. The text changes
    between operating systems and languages; exit code 0 always means a reply
    came back.

    Return DEGRADED, not DOWN, when ping fails. On a network that blocks ping, a
    failed ping is not evidence the host is down. The TCP check decides that.

    Handle two things going wrong with ping itself: it might not be installed,
    and it might hang. subprocess.run takes a timeout too.
    """
    ping = ping_command(host, count=1, timeout_seconds=timeout_seconds)

    try:
        result = subprocess.run(ping, capture_output=True, text=True, timeout=timeout_seconds)
        return CheckResult(OK if result.returncode == 0 else DEGRADED, f"{name}: ping returned {result.returncode}")

    except subprocess.TimeoutExpired:
        return CheckResult(DEGRADED, f"{name}: ping timed out after {timeout_seconds} seconds")
    except FileNotFoundError:
        return CheckResult(DEGRADED, f"{name}: ping command not found on this system")
    except Exception as e:
        return CheckResult(DEGRADED, f"{name}: ping failed with exception: {e}")
    