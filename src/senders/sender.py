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
from queue import Queue, Empty
from logging import Logger, getLogger
import json

class Sender:
    """Generic sender"""
    _logger: Logger
    _run: bool
    _thread: Thread

    _relay_name: str
    _queue: Queue = None
    _polling_ms: int

    def __init__(self, relay_name: str, queue: Queue, polling_ms: int = 1000):
        self._logger = getLogger()
        self._run = False
        self._thread = None

        self._relay_name = relay_name
        self._queue = queue
        self._polling_ms = polling_ms

    def start(self):
        """Start the working thread"""
        self._logger.info(
            "Starting sender",
            extra={ 'component': 'SENDER' }
        )
        self._run = True
        self._thread = Thread(target=self.run)
        self._thread.start()

    def run(self):
        """Actual working function"""
        while self._run:
            try:
                (device, code, ts) = self._queue.get(True, self._polling_ms / 1000.0)
                self._logger.info(
                    "Sending scan %s", json.dumps({'code': code}),
                    extra={ 'component': 'SENDER' }
                )
                self._send(device, code, ts)
            except Empty:
                pass

    def _send(self, device, code, ts):
        pass

    def stop(self):
        """Stop the working thread"""
        self._logger.info(
            "Stopping sender",
            extra={ 'component': 'SENDER' }
        )
        self._run = False
        if self._thread:
            self._thread.join()
