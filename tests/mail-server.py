#!/usr/bin/env python3

# pylint: disable=broad-except,consider-using-f-string,duplicate-code,invalid-name,redefined-outer-name

#
#  This file is part of Slurm-Mail.
#
#  Slurm-Mail is a drop in replacement for Slurm's e-mails to give users
#  much more information about their jobs compared to the standard Slurm
#  e-mails.
#
#   Copyright (C) 2018-2022 Neil Munday (neil@mundayweb.com)
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
mail-server.py

Author: Neil Munday

Runs a simple receive only mail server on the given host and port.

Note: based on example from: https://aiosmtpd.readthedocs.io/en/latest/controller.html
"""

import argparse
import asyncio
import logging
import aiosmtpd.controller

logging.getLogger("mail.log").setLevel(logging.WARNING)

class TestHandler:
    """
    E-mail handler.
    """

    @staticmethod
    async def handle_RCPT(server, session, envelope, address, rcpt_options):
        """
        Handle receipt of e-mail.
        """
        # pylint: disable=unused-argument
        envelope.rcpt_tos.append(address)
        return "250 OK"

    @staticmethod
    async def handle_DATA(server, session, envelope):
        """
        Handle the e-mail itself.
        """
        # pylint: disable=unused-argument
        logging.info("New email!")
        logging.info("Message from %s", envelope.mail_from)
        logging.info("Message for %s", envelope.rcpt_tos)
        logging.info("Message data")
        for ln in envelope.content.decode("utf8", errors="replace").splitlines():
            logging.info(ln.strip())
        logging.info("End of message")
        return "250 Message accepted for delivery"

async def amain(loop, ip, port):
    """
    Asyc main function.
    """
    try:
        controller = aiosmtpd.controller.Controller(TestHandler(), hostname=ip, port=port)
        controller.start()
        logging.info("mail server listening on %s:%d", ip, port)
    except PermissionError as e:
        logging.error(e)
        controller.stop()
        loop.stop()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="A simple mail server for use when test Slurm Mail", add_help=True
    )
    parser.add_argument(
        "-i", "--ip", default="127.0.0.1", dest="ip",
        help="the port to listen on")
    parser.add_argument(
        "-p", "--port", type=int, default=25, dest="port",
        help="the port to listen on"
    )
    parser.add_argument(
        "-v", "--verbose", help="Turn on debug messages", dest="verbose",
        action="store_true"
    )
    args = parser.parse_args()

    log_date = "%Y/%m/%d %H:%M:%S"
    log_format = "%(asctime)s:%(levelname)s: %(message)s"

    if args.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logging.basicConfig(
        format=log_format, datefmt=log_date, level=log_level
    )

    loop = asyncio.get_event_loop()
    loop.create_task(amain(loop, args.ip, args.port))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
