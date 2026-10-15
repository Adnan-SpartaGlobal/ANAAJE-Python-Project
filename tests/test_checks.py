"""Tests for your health-check tool.

THESE TWO TESTS FAIL RIGHT NOW. That is deliberate, and it is where you start.

    pytest -q

You get two failures because nothing is implemented yet. Make them pass, then
keep going: these two show the shape, they are not the target.

The rule for this project, and it is not negotiable:

    You may use AI to draft a function. You write the test yourself, and it
    must pass.

A test you wrote is evidence. A function you accepted is a guess.

Tests worth adding, roughly in the order they will help you:

  - load_config rejects port: "8801" written in quotes.
  - load_config gives a ConfigError, not a raw YAML error, on a stray tab.
  - check_tcp reports a DNS failure differently from a refused connection.
  - worst_state returns DOWN when there is one DOWN among many OK results.
  - check_reported_disk at exactly the threshold - which side of the line is it?
  - check_http turns a 500 into DEGRADED and a timeout into DOWN.

That last one needs a fake response instead of a real server, so the test runs
with the fleet stopped and the Wi-Fi off. Look up unittest.mock.patch. Be
careful: a badly built mock passes whatever your code does. Before you trust a
passing test, break the code on purpose and check that the test fails.
"""

import socket

import pytest

from checks import DOWN
from checks.tcp import check_tcp
from config import ConfigError, load_config


def test_config_reports_every_problem_at_once(tmp_path):
    """A config with three faults should produce three complaints, not one.

    tmp_path is a pytest fixture: a fresh empty directory for this test only,
    removed afterwards. Use it whenever a test needs a file, so tests never
    touch your real targets.yaml.
    """
    broken = tmp_path / "targets.yaml"
    broken.write_text(
        "defaults:\n"
        "  disk_threshold_percent: 150\n"   # fault 1: over 100
        "targets:\n"
        "  - name: fleet-node-01\n"
        "    host: 127.0.0.1\n"
        "    port: 70000\n"                 # fault 2: not a valid port
        "  - name: fleet-node-02\n"
        "    host: 127.0.0.1\n",            # fault 3: no port at all
        encoding="utf-8",
    )

    with pytest.raises(ConfigError) as raised:
        load_config(broken)

    problems = raised.value.problems
    assert len(problems) >= 3, f"expected at least 3 problems, got {problems}"


def test_tcp_reports_refused_when_nothing_is_listening():
    """A port with nothing on it is DOWN, and the detail says why.

    Rather than trusting that some port happens to be free, this asks the
    operating system for a free port, then closes it straight away. Nothing is
    listening there now, so connecting to it is refused - on every machine,
    every time. Tests that depend on luck are worse than no tests.
    """
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))    # port 0 means "any free port"
        free_port = probe.getsockname()[1]

    result = check_tcp("test-node", "127.0.0.1", free_port, timeout=2)

    assert result.state == DOWN
    assert "refused" in result.detail.lower()
