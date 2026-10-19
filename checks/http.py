"""checks/http.py - is the service actually well? Extension tier.

The TCP check tells you a process is listening. This one asks it how it is.

YOU WRITE THIS. The signature and contract are fixed, because healthcheck.py
already calls it.
"""

from __future__ import annotations

import requests
from . import DEGRADED, DOWN, OK, CheckResult

CHECK_NAME = "http"


def check_http(name: str, url: str, timeout: float) -> CheckResult:
    """GET the health endpoint at url, and classify what came back.

    Use requests.get(url, timeout=timeout). The timeout is not optional:
    requests has NO default timeout and will wait forever without one. Node 8803
    exists to prove it.

    Four outcomes, and each is a different finding:

      HTTP 200 and the body says "status": "ok"   ->  OK
      any other status code, or a 200 whose body
        says something other than ok              ->  DEGRADED
      the request timed out                       ->  DOWN
      the connection failed (refused, DNS)        ->  DOWN

    Why is a 500 DEGRADED and not DOWN? Because you reached it and it answered.
    Something is listening, and it is telling you it is unwell. That needs a
    different person to do a different thing from a host that is not there.

    Put the useful part of the answer in `detail`. Node 8802 explains itself in
    its response body - "HTTP 500: database connection pool exhausted" is far
    more use to an engineer than "HTTP 500".

    When the check passes, put the parsed JSON body in extra={"payload": body}.
    The disk check reads the disk figures from there, so you only make one
    request per target, not two.

    Never raises. Catch the requests exceptions you expect, specifically. The
    requests exceptions are related to each other in the same way the socket
    ones are, so the order of your except blocks matters again.
    """
    extra = {}
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code != 200:
            state = DEGRADED
            detail = f"HTTP {response.status_code}, {response.text.strip()[:100] or 'no reason given'}"
        elif response.json().get("status") == "ok":
            state = OK
            detail = f"HTTP {response.status_code}, status ok"
            extra = {"payload": response.json()}
        else:
            state = DEGRADED
            detail = f"HTTP 200, status was {response.json().get("status")!r}"

    except requests.exceptions.JSONDecodeError:
        state = DEGRADED
        detail = f"HTTP {response.status_code}, JSON is invalid"

    except AttributeError:
        state = DEGRADED
        detail = f"HTTP {response.status_code}, body was not a JSON object"

    except requests.exceptions.Timeout:
        state =  DOWN
        detail = f"No response within {timeout}s"

    except requests.exceptions.ConnectionError as error:
        state = DOWN
        message = str(error).lower()
        if "refused" in message:
            detail = "Connection refused: nothing listening on that port"
        elif "resolve" in message or "name or service" in message or "nodename" in message:
            detail = "Could not resolve hostname"
        else:
            detail = "Connection failed"

    except requests.exceptions.RequestException as error:
        state = DOWN
        detail = f"unexpected request error ({type(error).__name__})"

    return CheckResult(name, CHECK_NAME, state, detail, extra=extra)