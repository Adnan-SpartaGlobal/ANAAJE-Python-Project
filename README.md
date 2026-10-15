# Server Health-Check CLI

A one-day group project. You will write a command-line tool that checks a fleet
of servers, tells you which ones are unwell and why, and reports the answer in
a form both people and pipelines can use.

## Timings

One day, in groups of three to five.

## Summary

You are given a small fleet of servers running on your own machine. Some of them
are healthy. Some are broken in specific, deliberate ways. Your job is to write
`healthcheck.py`, a tool that reads the list of servers from `targets.yaml`,
checks each one, and reports what it found to the console, to a log file and,
later, to a JSON report.

"Is it up?" turns out to have at least five different answers. A server can be
up and broken. It can be slow. It can be missing. Its name can fail to resolve.
A good health check tells those apart, because each one sends a different person
to look in a different place.

The tool ends with an exit code that a pipeline can act on:

```bash
python healthcheck.py && echo "DEPLOY"
```

The second command runs only if every server is healthy. That is a pipeline
gate, and you will have built one four weeks before you meet Jenkins.

## Before you start

Clone your team's repository, make a virtual environment and install what the
project needs:

```bash
git clone <your-team-repo-url> health-check
cd health-check
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Check the tests run. Two of them fail, which is where you start:

```bash
pytest -q
```

Start the fleet in its own terminal and leave it running:

```bash
python fleet/run_fleet.py
```

Then, in a second terminal, look at every node by hand **before you write any
Python**. You cannot automate a check you have never done yourself:

```bash
curl http://127.0.0.1:8801/health
curl http://127.0.0.1:8802/health
curl -m 3 http://127.0.0.1:8803/health
curl http://127.0.0.1:8804/health
```

Four commands, four different results. As a team, name each one. `fleet/README.md`
explains what every node is doing and why.

## What is in here

```
healthcheck.py       the entry point. Arguments, logging and the run are wired up.
targets.yaml         the fleet. Your team adds keys to it as you build each check.
config.py            you write this. Load and validate targets.yaml.
checks/__init__.py   the shared result shape every check returns. Complete - read it.
checks/tcp.py        you write this. Core tier.
checks/http.py       you write this. Extension tier.
checks/disk.py       you write this. Extension tier.
checks/ping.py       you write this. Stretch tier.
report.py            you write this. The console table and the JSON report.
alerts.py            you write this. Stretch tier.
fleet/               the fake servers you check. Do not edit.
tests/               two failing tests to start you off
```

Each file you write has its functions already named, with the contract written
in the docstring and a `TODO` where the work goes. The function names and
arguments are fixed, because other files already call them. That is what lets
four of you work at once.

Run `python healthcheck.py` at any point. Until everything is written it stops
at the first unfinished function and tells you which one.

## What you are building

### 1. Read and validate the fleet

`config.py`. Read `targets.yaml` and refuse to go any further if anything in it
is wrong.

Report **every** problem at once. Someone with three mistakes in the file should
learn about all three in one run. Work up from "the file exists and is valid
YAML", through "every target has the keys it needs", to "the values make sense":
a port is a whole number from 1 to 65535, a threshold is from 1 to 100, a URL
starts with `http`.

All of this happens before a single network call. A run that fails here has
contacted nothing and changed nothing.

The first thing your team ships is the simplest: load `targets.yaml` and list
the targets. `healthcheck.py` already prints them once `load_config()` works.

### 2. Is anything listening?

`checks/tcp.py`. Open a TCP connection to each target's host and port with
`socket.create_connection`, with a timeout, and close it again.

This is the cheapest possible check. It will tell you that 8804 is refusing
connections, and that `fleet-node-05.invalid` does not exist. Tell those apart:
they are different exceptions and different findings.

Then run it against node 02. It reports healthy. It is not.

### 3. Is it actually well?

`checks/http.py`. Ask each target's `/health` endpoint how it is, using
`requests`, **with a timeout**.

| What you get | State | What it means |
|---|---|---|
| `200` and `"status": "ok"` | `OK` | Healthy |
| `500`, or any other status | `DEGRADED` | Something is listening, and it is telling you it is unwell |
| Timed out | `DOWN` | It never answered |
| Connection refused, or the name did not resolve | `DOWN` | You never reached it |

`requests` has no default timeout. Without one, node 03 holds your entire run
hostage for ten seconds. In production, the wait can be forever.

### 4. Is the disk filling up?

`checks/disk.py`. The healthy nodes report their own disk usage in their
`/health` response. Read the figure and compare it with
`disk_threshold_percent` from `targets.yaml`.

The threshold lives in the config file, not in your code. Lower it to 40 and run
again: the same reading from node 01 now crosses the line. Thresholds are
configuration, for the same reason a port number is.

`check_local_disk` uses `shutil.disk_usage` to check the machine your tool runs
on. Label it honestly. It is the only disk your tool can see directly.

### 5. Report, log, and exit

`report.py` and the parts of `healthcheck.py` marked `TODO`.

Print a table a human can read at a glance. With `--json-report`, also write a
JSON file another program could read. Use the `logging` module, not `print`,
for everything that is not the table. The log goes to the console and to
`healthcheck.log`.

The test to set yourself: **could a teammate who was not there work out what
happened from `healthcheck.log` alone?**

Humans read logs. Machines read exit codes:

| Code | Meaning |
|---|---|
| 0 | Every target healthy |
| 1 | Something degraded, or the config is invalid |
| 2 | Something down |

These are fixed. Do not invent a fourth code. If your team thinks one is needed,
argue for it in your demo.

## Difficulty tiers

Work through them in order. Finishing a tier properly beats starting the next
one badly.

**Core.** Load and validate `targets.yaml`. Run the TCP check against every
target. Print a readable table showing each target, whether it is reachable,
and the reason when it is not. No HTTP, no disk, no report file. Every group is
expected to get here, and a group that ships this has genuinely succeeded.

**Extension.** Add the HTTP check with a timeout, telling 200 from 500 from
timed out from refused from unresolvable. Add the disk check against the
configured threshold. Add `--json-report`. Implement the exit-code contract.
Then uncomment the `github-api` target in `targets.yaml` and watch a real
network call behave differently from a local one. This is the standard to aim
for.

**Stretch.** Add the `ping` check, using `subprocess` and `platform.system()` to
pick the right flags. If `ping` fails on your network while the TCP check works,
that is a finding to report, not a bug to fix. Many networks block it.

Start the fleet with `--webhook` and post an alert to the receiver
on port 8805 when anything is wrong, with the URL read from the
`HEALTHCHECK_WEBHOOK_URL` environment variable, never from `targets.yaml`. Add a
retry budget before declaring a target down, and be ready to defend your numbers.
Add the `fleet-node-05.invalid` target. Put the date and time in the report file
name and report what has **changed** since the previous run.

Something to think about for the demo, not to build: raise the timeout to 12
seconds so node 03 answers, and the whole run takes over ten seconds, nearly all
of it waiting on one node. Your tool checks targets one after another. With 200
targets, how long could a run take, and how would you fix that?

## User stories

Your backlog. Split these across the team. The module boundaries are drawn so
that one person can own each check without colliding with the others.

```
#1  As an engineer, I can run healthcheck.py and see every target in
    targets.yaml listed.
#2  As an engineer, I am told every problem in targets.yaml in one run, before
    any server is contacted.
#3  As an engineer, I can see which targets are not accepting connections, and
    whether that is because nothing is listening or because the name does not
    resolve.
#4  As an engineer, I can see which targets are reachable but unhealthy, and the
    reason each one gives.
#5  As an engineer, a target that does not answer cannot hold up the whole run.
#6  As an engineer, I am warned when a target's disk is over the threshold set
    in targets.yaml.
#7  As an on-call engineer, I can read healthcheck.log and reconstruct what was
    checked and what was found without having been there.
#8  As a pipeline, I can rely on healthcheck.py's exit code to decide whether to
    deploy.
#9  As a team, we are alerted when something is wrong, without the alert URL
    ever being committed to the repository.
```

Write at least one of these up as an epic. Add acceptance criteria to each story
as you pick it up.

## Acceptance criteria

**Core**

- `healthcheck.py` runs without a traceback on both a valid and an invalid
  `targets.yaml`
- an invalid config exits 1, names every problem in one run, and makes no
  network call
- `port: "8801"` in quotes is rejected as not a whole number
- every target appears in a table with its TCP result
- 8804 is reported as refused, and the reason is shown

**Extension**

- node 02 is reported as degraded, with the reason from its response body
- node 03 is reported as down by timeout, within the configured timeout, not
  after ten seconds
- refused, timed out, HTTP 500 and DNS failure are each reported differently
- the disk threshold is read from `targets.yaml`, and changing it changes the
  verdict without any code change
- `--json-report` writes a valid JSON file
- `healthcheck.log` has a timestamp and level on every line
- the exit code follows the contract, and
  `python healthcheck.py && echo "DEPLOY"` prints only when everything is healthy

**Stretch**

- `--ping` picks its flags by platform, and a blocked ping is reported rather
  than crashing the run
- an alert arrives at the receiver on 8805 when something is wrong, and not when
  everything is healthy
- the webhook URL appears nowhere in the repository
- the tool does not crash when the receiver is not running
- any retry budget is configurable and the group can explain its numbers

**Team**

- every change reached `main` through a pull request with at least one review
- the backlog exists as user stories, with at least one epic
- a definition of done and a definition of ready are written down
- the README explains what the tool is, how to install it, how to run it, and
  credits everyone who worked on it
- the team wrote its own tests, beyond the two supplied, and they pass

## How your team works

Read `CONTRIBUTING.md` before anyone writes any code. Protected `main`, feature
branches, pull requests, one review before merge.

You will get a merge conflict on `targets.yaml`, because every check needs its
own key in it and four of you will add them on four branches at the same time.
That is not a mistake in the plan. Resolving one calmly, as a group, with the
clock running, is one of the most useful things you will do this week.

## The rule about AI

You may use AI to help draft a function. **You write the test yourself, and it
must pass.**

Be especially careful with tests that fake the network. AI tools write those
confidently, and a badly built fake passes no matter what your code does. A
green test that tests nothing is worse than no test, because you believe it.
Before you trust a passing test, break the code on purpose and check that the
test goes red.

Reviewing code you did not write, and proving it works, is a real part of a
junior engineer's job. A test you wrote is evidence. A function you accepted is
a guess.

## Demo

Five minutes at the end of the day. Run the tool against the full fleet with
`healthcheck.log` on screen, and walk through what each finding means. Then show
the pipeline gate: run it with node 04 missing and nothing deploys.

Be ready to answer: which of these findings would you want to be woken up for
at 3am, and which could wait until morning?
