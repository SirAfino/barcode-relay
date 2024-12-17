# 
# This file is part of the BarcodeRelay distribution (https://github.com/SirAfino/barcode-relay).
# Copyright (c) 2024 Gabriele Serafino.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from threading import Thread
from logging import Logger, getLogger
from time import sleep, time

class Hearthbeat:
    """Generic hearthbeat"""
    _logger: Logger
    _run: bool
    _thread: Thread

    _relay_name: str
    _polling_ms: int
    _hb_interval_ms: int

    def __init__(self, relay_name: str, hb_interval_ms: int = 10000, polling_ms: int = 1000):
        self._logger = getLogger()
        self._run = False
        self._thread = None

        self._relay_name = relay_name
        self._polling_ms = polling_ms
        self._hb_interval_ms = hb_interval_ms

    def start(self):
        """Start the working thread"""
        self._logger.info(
            "Starting hearthbeat",
            extra={ 'component': 'HEARTHBEAT' }
        )
        self._run = True
        self._thread = Thread(target=self.run)
        self._thread.start()

    def run(self):
        """Actual working function"""
        last_hb = time()
        while self._run:
            if time() - last_hb >= (self._hb_interval_ms / 1000.0):
                self._send()
                last_hb = time()
            sleep(self._polling_ms / 1000.0)

    def _send(self):
        pass

    def stop(self):
        """Stop the working thread"""
        self._logger.info(
            "Stopping hearthbeat",
            extra={ 'component': 'HEARTHBEAT' }
        )
        self._run = False
        if self._thread:
            self._thread.join()
