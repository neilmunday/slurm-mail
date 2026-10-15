# pylint: disable=missing-function-docstring

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
Unit tests for slurmmail.ratelimit
"""

import json
import logging

from slurmmail.ratelimit import RateLimiter, RateLimitResult, get_period_str

ALLOW = RateLimitResult.ALLOW
LIMIT_REACHED = RateLimitResult.LIMIT_REACHED
LIMITED = RateLimitResult.LIMITED


def send(limiter: RateLimiter, recipient: str, now: float) -> RateLimitResult:
    result = limiter.check(recipient, now)
    if result == ALLOW:
        limiter.record(recipient, now)
    return result


def test_get_period_str():
    assert get_period_str(0) == "0 seconds"
    assert get_period_str(1) == "1 second"
    assert get_period_str(60) == "1 minute"
    assert get_period_str(3600) == "1 hour"
    assert get_period_str(5400) == "1 hour 30 minutes"
    assert get_period_str(172861) == "2 days 1 minute 1 second"


class TestRateLimiter:
    """
    Test RateLimiter
    """

    def test_limit(self, tmp_path):
        limiter = RateLimiter(tmp_path / "state.json", 3, 60)
        assert [send(limiter, "a@example.com", t) for t in [0, 1, 2]] == [ALLOW] * 3
        assert send(limiter, "a@example.com", 3) == LIMIT_REACHED
        assert send(limiter, "a@example.com", 4) == LIMITED
        # other recipients are unaffected
        assert send(limiter, "b@example.com", 5) == ALLOW

    def test_recipient_case_insensitive(self, tmp_path):
        limiter = RateLimiter(tmp_path / "state.json", 1, 60)
        assert send(limiter, "A@Example.com", 0) == ALLOW
        assert send(limiter, " a@example.com", 1) == LIMIT_REACHED

    def test_sliding_window(self, tmp_path):
        limiter = RateLimiter(tmp_path / "state.json", 2, 60)
        assert send(limiter, "a@example.com", 0) == ALLOW
        assert send(limiter, "a@example.com", 30) == ALLOW
        # first e-mail has left the window
        assert send(limiter, "a@example.com", 61) == ALLOW

    def test_stays_blocked_while_flooding(self, tmp_path):
        limiter = RateLimiter(tmp_path / "state.json", 2, 60)
        send(limiter, "a@example.com", 0)
        send(limiter, "a@example.com", 1)
        assert send(limiter, "a@example.com", 2) == LIMIT_REACHED
        # requests keep arriving, so the address stays blocked even though
        # the e-mails that were sent have left the window
        for t in range(30, 300, 30):
            assert send(limiter, "a@example.com", t) == LIMITED

    def test_unblocked_after_quiet_period(self, tmp_path, caplog):
        caplog.set_level(logging.INFO)
        limiter = RateLimiter(tmp_path / "state.json", 1, 60)
        send(limiter, "a@example.com", 0)
        assert send(limiter, "a@example.com", 1) == LIMIT_REACHED
        assert send(limiter, "a@example.com", 2) == LIMITED
        assert send(limiter, "a@example.com", 61) == LIMITED
        assert send(limiter, "a@example.com", 121) == ALLOW
        assert "Rate limit for a@example.com lifted: 3 e-mail(s) were suppressed" in caplog.text

    def test_save_and_load(self, tmp_path):
        state_file = tmp_path / "state.json"
        limiter = RateLimiter(state_file, 2, 60)
        send(limiter, "a@example.com", 0)
        send(limiter, "a@example.com", 1)
        send(limiter, "a@example.com", 2)
        send(limiter, "b@example.com", 10)
        limiter.save(now=30)

        limiter = RateLimiter(state_file, 2, 60)
        limiter.load()
        assert send(limiter, "a@example.com", 40) == LIMITED
        assert send(limiter, "b@example.com", 40) == ALLOW
        assert send(limiter, "b@example.com", 41) == LIMIT_REACHED

    def test_save_prunes_expired(self, tmp_path):
        state_file = tmp_path / "state.json"
        limiter = RateLimiter(state_file, 1, 60)
        send(limiter, "a@example.com", 0)
        send(limiter, "a@example.com", 1)  # blocked
        send(limiter, "b@example.com", 0)
        send(limiter, "c@example.com", 100)
        limiter.save(now=120)
        with state_file.open() as f:
            assert list(json.load(f)["recipients"]) == ["c@example.com"]

    def test_load_missing_file(self, tmp_path):
        limiter = RateLimiter(tmp_path / "state.json", 1, 60)
        limiter.load()
        assert send(limiter, "a@example.com", 0) == ALLOW

    def test_load_corrupt_file(self, tmp_path, caplog):
        state_file = tmp_path / "state.json"
        state_file.write_text("not json")
        limiter = RateLimiter(state_file, 1, 60)
        limiter.load()
        assert "Could not read rate limit state" in caplog.text
        assert send(limiter, "a@example.com", 0) == ALLOW

    def test_load_unexpected_format(self, tmp_path, caplog):
        state_file = tmp_path / "state.json"
        state_file.write_text("[]")
        limiter = RateLimiter(state_file, 1, 60)
        limiter.load()
        assert "Could not read rate limit state" in caplog.text
