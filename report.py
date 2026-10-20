"""report.py - turn a list of CheckResults into something people and programs can read.

Two audiences, two formats. The console table is for the person running the
tool right now. The JSON report is for whatever reads it next: another script,
a ticket, or the same tool tomorrow comparing today against yesterday.

Neither replaces the log file. The log says what happened and when. The report
says what was true at the end.

YOU WRITE THIS. The signatures are fixed, because healthcheck.py and alerts.py
already call them.
"""

from __future__ import annotations
import json

from pathlib import Path

from checks import DEGRADED, DOWN, OK, CheckResult

import json

from datetime import datetime


def worst_state(results: list[CheckResult]) -> str:
    """The overall verdict for the whole run. DOWN beats DEGRADED beats OK.

    This one function decides your tool's exit code, so it is worth a test.
    Core tier.
    """
    # TODO
    worst_state = ''
    for result in results:
        if result.state == DEGRADED:
            return DEGRADED
        elif result.state == DOWN:
            worst_state = DOWN
        else:
            if worst_state != DOWN:
                worst_state = OK
    return worst_state            



def render_table(results: list[CheckResult]) -> str:
    """Return a plain-text table of every check, one row per result. Core tier.

    Something like:

        TARGET         CHECK  STATE     DETAIL
        fleet-node-01  tcp    OK        connected to 127.0.0.1:8801
        fleet-node-04  tcp    DOWN      connection refused by 127.0.0.1:8804

    Return the string rather than printing it, so it is easy to test.

    Keep the columns lined up with f-string widths, such as f"{name:<15}".
    Avoid colour codes: they turn into junk characters in some Windows
    terminals and in any file the output is saved to.
    """
    # TODO
    summary_text_table = f" \n-------- FIRST TARGET ----------- \n{'TARGET':<15} {'CHECK':<6} {'STATE':<9} DETAIL\n"
    name = results[0].target
    for result in results:
        if result.target != name: summary_text_table += "\n-------- NEXT TARGET ----------- \n"
        name = result.target
        summary_text_table += f"{result.target:<15} {result.check:<6} {result.state:<9} {result.detail}\n"
        if result.extra != {}:
            summary_text_table += f"Additional Info: {result.extra} \n"
    return summary_text_table


def summarise(results: list[CheckResult]) -> dict:
    """Count results by state: {"OK": 7, "DEGRADED": 2, "DOWN": 3}. Core tier."""
    # TODO
    summary_dict = {"OK":0, "DEGRADED":0, "DOWN": 0}
    for result in results:
        summary_dict[result.state] += 1

    return summary_dict
 


def write_json_report(results: list[CheckResult], path: Path) -> Path:
    """Write a structured JSON report to path, and return the path. Extension tier.

    Include at least: when the report was generated, the overall state, the
    summary counts, and every result (CheckResult.as_dict() does the work).

    Use pathlib to create the parent directory if it does not exist, and write
    the file with a context manager or Path.write_text.

    Make the timestamp timezone-aware, in UTC. A local time with no zone in an
    incident report is a real hazard: two people in different places read the
    same file and disagree about when it happened.
    """
    # TODO

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(
            [result.__dict__ for result in results],
            file,
            indent=2,
        )
        json.dump(results, file, indent=2)

    return output_path


    # raise NotImplementedError("write_json_report() in report.py is not written yet")
