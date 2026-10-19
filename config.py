"""config.py - load targets.yaml and refuse to go on if it is wrong. Core tier.

This is the first thing your tool does, and the most important. A tool that
starts checking a fleet with a broken config produces confident nonsense.

YOU WRITE load_config(). ConfigError and Config are given, because
healthcheck.py already depends on their shape.
"""

from __future__ import annotations
import yaml
from pathlib import Path

# Used if targets.yaml has no defaults block yet. Your team decides whether
# these numbers are right - they are a starting point, not an answer.
DEFAULT_TIMEOUT_SECONDS = 2.0
DEFAULT_DISK_THRESHOLD_PERCENT = 85

required_keys = ("name", "host") 

class ConfigError(Exception):
    """Raised when the config cannot be used. Carries EVERY problem found."""

    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("; ".join(problems))


class Config:
    """A validated config. If you are holding one, it is safe to use."""

    def __init__(self, targets: list[dict], timeout_seconds: float,
                 disk_threshold_percent: int):
        self.targets = targets
        self.timeout_seconds = timeout_seconds
        self.disk_threshold_percent = disk_threshold_percent

    def __repr__(self) -> str:
        return (f"Config(targets={len(self.targets)}, "
                f"timeout_seconds={self.timeout_seconds}, "
                f"disk_threshold_percent={self.disk_threshold_percent})")


def load_config(path: Path) -> Config:
    """Read targets.yaml, validate it, and return a Config.

    Raises ConfigError listing EVERY problem found, not only the first one.
    Someone with three mistakes in the file should learn about all three in one
    run, not fix one, re-run, and find the next.

    The pattern that makes that possible: start with an empty list called
    problems, append to it every time you find something wrong, and raise
    ConfigError(problems) once at the very end if the list is not empty.

    Work up through these levels:

      1. The file exists, and it is valid YAML. A stray tab should give a clear
         message, not a traceback. Use yaml.safe_load, never yaml.load.
      2. There is a `targets` list and it is not empty.
      3. Every target has a name and a host. Once your team adds port, every
         target needs that too.
      4. The values make sense. A port is a whole number from 1 to 65535 - and
         watch out for port: "8801" in quotes, which YAML reads as text. A
         health_url starts with http. A timeout is a positive number. A disk
         threshold is a whole number from 1 to 100.

    All of this happens before a single network call. A run that fails here has
    contacted nothing and changed nothing, which is why it can stop cleanly.
    """
    # TODO
    try:
        with open(path, "r", encoding="utf-8") as file:
            text_yaml = yaml.safe_load(file)
    except FileNotFoundError as error:
        raise ConfigError(f"File could not be found. {error}")
    except PermissionError as error:
        raise ConfigError(f"Cannot read config file: {error}")
    except yaml.YAMLError as error:
        raise ConfigError(f"Invalid YAML: {error}")

    targets = text_yaml["targets"]
    if targets is None:
        raise ConfigError(f"Yaml file is empty")

    validate(targets)
    return Config(targets=targets, timeout_seconds=2, disk_threshold_percent= 80)

def validate(targets):
    faults = []

    for target in targets:
        for keys in required_keys:
            if keys not in target:
                faults.append(f"Missing Key: {keys}")
        if faults:
            raise ConfigError(faults)
    
