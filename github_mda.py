#!/usr/bin/python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

""" Github Mail Delivery Agent

This module is a simple mail delivery agent for relaying messages to
a Github Enterprise instance. Specifically it relays messages that are
replies or comments to pull request or issues.

It expects the entire raw message on STDIN.
To use this with fetchmail put this line in your .fetchmailrc
mda /path/to/this/script.py

"""

__author__  = "Raju Subramanian <coder@mahesh.net>"

import email.utils
from email.parser import Parser
import fileinput
import logging
import os
import re
import shutil
import smtplib

BASE_DIR = '/var/github-fetchmail'
REPLY_SUBDOMAIN = 'reply.github.priv.mycompany.net'
SMTP_HOST = 'github.mv.mycompany.net'
LOG_FILENAME = os.path.join(
    BASE_DIR, os.path.splitext(os.path.basename(__file__))[0] + ".log")

# pylint: disable=C0103
logger = logging.getLogger('github_mda')
logger.setLevel(logging.DEBUG)

# Log INFO and higher to log file
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
fh = logging.FileHandler(LOG_FILENAME)
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)
logger.addHandler(fh)


class MailDeliveryAgent(object):
    """This class encapsulates the basic functions of the github mda."""

    def __init__(self):
        self.__message = None
        self.__re_pattern = re.compile(r'\s*reply\+\w+@%s\s*' % REPLY_SUBDOMAIN)
        self.__msg_file = None
        # Set up required directories
        for mail_dir in ['incoming', 'processed', 'ignored']:
            full_path = os.path.join(BASE_DIR, mail_dir)
            if not os.path.exists(full_path):
                os.makedirs(full_path)

    def parse_address_field(self, field):
        """Parses an address field and returns the part before '@'"""
        value = email.utils.parseaddr(self.__message[field])[1]
        return value.split('@')[0]

    def receive_message(self):
        """Reads the raw message from stdin

        This function first reads the raw message from stdin and parses into an
        email.message.Message object. It also writes out the raw data to a file.
        """
        lines = []
        for line in fileinput.input():
            lines.append(line)
        raw_email = ''.join(lines)
        parser = Parser()
        self.__message = parser.parsestr(raw_email)

        # Write out the raw email
        epoch = email.utils.mktime_tz(
            email.utils.parsedate_tz(self.__message['Date']))
        addr_from = self.parse_address_field('From')

        if 'In-Reply-To' in self.__message:
            in_reply_to = self.parse_address_field(
                'In-Reply-To').replace('/', '_')
            epoch = email.utils.mktime_tz(
                email.utils.parsedate_tz(self.__message['Date']))
            addr_from = self.parse_address_field('From')
            self.__msg_file = '%s-%s-%s' % (in_reply_to, addr_from, epoch)
        else:
            self.__msg_file = '%s-%s' % (addr_from, epoch)

        filepath = os.path.join(BASE_DIR, 'incoming', self.__msg_file)
        logger.info("Writing raw message to %s", filepath)
        with open(filepath, 'w+') as outfile:
            outfile.write(raw_email)

    def forward_message(self):
        """Forwards the parsed message to a SMTP Host."""
        if not self.__message:
            logger.error("No message to forward")
            return

        to_list = []
        for dest in self.__message.get_all('to', []):
            if self.__re_pattern.match(email.utils.parseaddr(dest)[1]):
                to_list.append(dest)
        logger.info("Forwarding message for %s to %s", to_list, SMTP_HOST)
        smtp = smtplib.SMTP(SMTP_HOST)
        try:
            smtp.sendmail(self.__message['From'], to_list,
                          self.__message.as_string())
        except Exception, e:
            logger.error("SMTP Send failed: %s", e)
            return
        finally:
            smtp.quit()
        logger.info("SMTP Send successful")

        if to_list:
            self.move_file_to('processed')
        else:
            self.move_file_to('ignored')

    def move_file_to(self, dest_dir):
        """Moves a file from 'incoming' to dest_dir."""
        src = os.path.join(BASE_DIR, 'incoming', self.__msg_file)
        dst = os.path.join(BASE_DIR, dest_dir, self.__msg_file)
        logger.info("Moving incoming/%s to %s", self.__msg_file, dest_dir)
        shutil.move(src, dst)

    def process(self):
        """Process the incoming message."""
        self.receive_message()
        self.forward_message()


if __name__ == '__main__':
    MailDeliveryAgent().process()
