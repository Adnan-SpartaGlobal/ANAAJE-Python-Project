# The fake fleet

Four pretend servers and an alert receiver, all running on your own machine.
Your health-check tool checks these. You do not edit them.

**Several of them are broken on purpose.** If your tool reports a problem with
node 02, 03 or 04, your tool is probably working. If it reports a problem with
node 01, the bug is in your tool.

## Starting and stopping it

From the root of the repository, with your virtual environment active:

```bash
python fleet/run_fleet.py
```

Leave that terminal running and open a second one for your own work. Press
Ctrl+C in the first terminal to stop the fleet.

For the stretch tier, also start the alert receiver:

```bash
python fleet/run_fleet.py --webhook
```

Check the fleet is up before you write any Python:

```bash
curl http://127.0.0.1:8801/health
curl http://127.0.0.1:8802/health
curl -m 3 http://127.0.0.1:8803/health
curl http://127.0.0.1:8804/health
```

Each of those behaves differently. Work out why from the table below before you
move on.

## What each node does

| Target | Port | Behaviour | What it teaches |
|---|---|---|---|
| `fleet-node-01` | 8801 | Answers `200` with `"status": "ok"` and disk at 41% | The healthy baseline |
| `fleet-node-02` | 8802 | Answers `500` with a reason in the body | Up but broken. A port check calls this healthy. It is not. |
| `fleet-node-03` | 8803 | Waits ten seconds, then answers `200` with disk at 91% | Timeouts. Also: two problems can hide behind each other. |
| `fleet-node-04` | 8804 | Not started. Nothing is listening. | Connection refused |
| `fleet-node-05` | none | The name `fleet-node-05.invalid` can never resolve | DNS failure, which is not the same as refused |

"Down" is not one thing. An engineer who can tell refused from timed out from
HTTP 500 from "that name does not exist" already knows where to start looking,
and that is most of the job on a support desk.

## The disk figures are fixtures

Nodes 01 and 03 report their disk usage in their `/health` response. The numbers
are fixed in the code so everyone in the room gets the same result. They are
not readings from a real disk.

The **shape** is real. A real service reports its own disk in its health
response because nothing outside the machine can measure it. Your tool cannot
read another machine's disk with `shutil.disk_usage`. It can only read the
figure the machine reports about itself.

## Reading the code

You are welcome to. Each node is short, commented, and written the way you
should write your own Python: `logging` rather than `print`, f-strings, and
`pathlib` for paths.

`run_fleet.py` uses `subprocess` to start the other nodes as separate programs.
That is worth reading when you reach the `ping` check in the stretch tier.

Nothing in here shows you how to **check** a server. These are the servers, not
the checks.

## Something is wrong with the fleet itself

**"Address already in use"** means something is already on that port, usually a
fleet you started earlier and did not stop. Find it and stop it:

```bash
lsof -i :8801          # macOS and Linux
netstat -ano | findstr :8801     # Windows
```

**A Windows firewall prompt** may appear the first time the fleet starts. The
fleet only listens on `127.0.0.1`, your own machine, so allowing it for private
networks is enough.

**`ModuleNotFoundError: No module named 'flask'`** means your virtual
environment is not active, or you have not run `pip install -r requirements.txt`
inside it. If Flask genuinely will not install, tell your trainer.

## Why these are processes and not containers

Today the fleet is four Python processes on your machine. In Week 8 you will
run the same kind of fleet as containers. **Your check code will not need to
change**, because it talks to the fleet over the network, by host and port, and
never pokes at the processes directly. That is the whole argument for checking
services through their network interface.
