#
#  This file is part of Slurm-Mail.
#
#  Slurm-Mail is a drop in replacement for Slurm's e-mails to give users
#  much more information about their jobs compared to the standard Slurm
#  e-mails.
#
#   Copyright (C) 2018-2026 Neil Munday (neil@mundayweb.com)
#
#  Slurm-Mail is free software: you can redistribute it and/or modify it
#  under the terms of the GNU General Public License as published by the
#  Free Software Foundation, either version 3 of the License, or (at
#  your option) any later version.
#
#  Slurm-Mail is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Slurm-Mail.  If not, see <http://www.gnu.org/licenses/>.
#

"""
This module provides per recipient e-mail rate limiting for Slurm-Mail.

A recipient may be sent at most `max_emails` e-mails within a sliding
window of `period` seconds. Once that limit is reached the recipient is
blocked and all further e-mails are suppressed until no e-mails have been
requested for that recipient for `period` seconds. This means a runaway
job submission loop results in at most `max_emails` e-mails (plus an
optional notification) rather than one e-mail per job.

State is persisted to a JSON file between runs of `slurm-send-mail`.
"""

import json
import logging
import os
import pathlib
import time

from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

DEFAULT_RATE_LIMIT_PERIOD = 3600


class RateLimitResult(Enum):
    """
    Results of `RateLimiter.check`.
    """
    ALLOW = "allow"
    LIMIT_REACHED = "limit_reached"  # recipient has just been blocked
    LIMITED = "limited"  # recipient was already blocked


def get_period_str(seconds: int) -> str:
    """
    Convert the given number of seconds into a human readable string,
    e.g. 5400 -> "1 hour 30 minutes".
    """
    parts = []
    for name, unit in [("day", 86400), ("hour", 3600), ("minute", 60), ("second", 1)]:
        value, seconds = divmod(seconds, unit)
        if value > 0:
            parts.append(f"{value} {name}{'s' if value > 1 else ''}")
    if not parts:
        return "0 seconds"
    return " ".join(parts)


class RateLimiter:
    """
    Tracks how many e-mails have been sent to each recipient and decides
    whether further e-mails should be sent.
    """

    def __init__(self, state_file: pathlib.Path, max_emails: int, period: int) -> None:
        self.state_file = state_file
        self.max_emails = max_emails
        self.period = period
        self.__recipients: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def __key(recipient: str) -> str:
        return recipient.strip().lower()

    def load(self) -> None:
        """
        Load state from the state file. A missing or unreadable state
        file results in an empty state.
        """
        self.__recipients = {}
        if not self.state_file.exists():
            return
        try:
            with self.state_file.open(encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict) or not isinstance(data.get("recipients"), dict):
                raise ValueError("unexpected format")
            self.__recipients = data["recipients"]
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Could not read rate limit state from %s, starting afresh: %s", self.state_file, e)

    def save(self, now: Optional[float] = None) -> None:
        """
        Write state to the state file, discarding recipients that no
        longer need to be tracked.
        """
        self.__prune(now)
        tmp_file = self.state_file.with_name(self.state_file.name + ".tmp")
        with tmp_file.open(mode="w", encoding="utf-8") as f:
            json.dump({"recipients": self.__recipients}, f)
        os.replace(tmp_file, self.state_file)

    def __expire(self, key: str, now: float) -> None:
        entry = self.__recipients[key]
        entry["sent"] = [ts for ts in entry.get("sent", []) if ts > now - self.period]
        if entry.get("blocked") and now - entry.get("last_suppressed", 0) >= self.period:
            logger.info(
                "Rate limit for %s lifted: %d e-mail(s) were suppressed",
                key,
                entry.get("suppressed", 0),
            )
            for field in ["blocked", "last_suppressed", "suppressed"]:
                entry.pop(field, None)

    def __prune(self, now: Optional[float] = None) -> None:
        if now is None:
            now = time.time()
        for key in list(self.__recipients):
            self.__expire(key, now)
            entry = self.__recipients[key]
            if not entry["sent"] and not entry.get("blocked"):
                del self.__recipients[key]

    def check(self, recipient: str, now: Optional[float] = None) -> RateLimitResult:
        """
        Determine whether an e-mail may be sent to the given recipient.

        Returns ALLOW if the e-mail may be sent, LIMIT_REACHED if the
        recipient has just exceeded the limit, or LIMITED if the recipient
        was already blocked. In the latter two cases the suppressed e-mail
        is recorded.
        """
        if now is None:
            now = time.time()
        key = self.__key(recipient)
        entry = self.__recipients.setdefault(key, {"sent": []})
        self.__expire(key, now)

        if entry.get("blocked"):
            entry["last_suppressed"] = now
            entry["suppressed"] = entry.get("suppressed", 0) + 1
            return RateLimitResult.LIMITED

        if len(entry["sent"]) >= self.max_emails:
            entry["blocked"] = True
            entry["last_suppressed"] = now
            entry["suppressed"] = 1
            return RateLimitResult.LIMIT_REACHED

        return RateLimitResult.ALLOW

    def record(self, recipient: str, now: Optional[float] = None) -> None:
        """
        Record that an e-mail has been sent to the given recipient.
        """
        if now is None:
            now = time.time()
        entry = self.__recipients.setdefault(self.__key(recipient), {"sent": []})
        entry["sent"].append(now)
