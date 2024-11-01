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

from logging import Logger, getLogger
from queue import Queue
from threading import Thread

from device_config import DeviceConfig

class DeviceReader:
    """Generic device reader"""
    _logger: Logger
    _run: bool
    _thread: Thread
    _queue: Queue

    _config: DeviceConfig
    _polling_ms: int

    def __init__(self, config: DeviceConfig, queue: Queue, polling_ms: int = 1000) -> None:
        self._logger = getLogger()
        self._run = False
        self._thread = None

        self._config = config
        self._queue = queue
        self._polling_ms = polling_ms

    def start(self):
        """Start the reader thread"""
        self._logger.info(
            "Starting receiver",
            extra={ 'component': 'READER' }
        )
        self._run = True
        self._thread = Thread(target=self.run)
        self._thread.start()

    def run(self):
        """Actual reader working function"""

    def stop(self):
        """Stop the reader thread"""
        self._logger.info(
            "Stopping receiver",
            extra={ 'component': 'READER' }
        )
        self._run = False
        if self._thread:
            self._thread.join()
