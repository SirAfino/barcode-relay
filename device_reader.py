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

# Generic device reader class
class DeviceReader:
    _logger: Logger
    _run: bool
    _thread: Thread
    _queue: Queue

    _hwid_regex: str
    _full_scan_regex: str
    _polling_ms: int

    def __init__(self, hwid_regex: str, full_string_regex: str, queue: Queue, polling_ms: int = 1000) -> None:
        self._logger = getLogger()
        self._run = False
        
        self._hwid_regex = hwid_regex
        self._full_scan_regex = full_string_regex
        self._queue = queue
        self._polling_ms = polling_ms

    def start(self):
        self._logger.info(
            f"Starting receiver ({self._hwid_regex})"
        )
        self._run = True
        self._thread = Thread(target=self.run)
        self._thread.start()
    
    def run(self):
        pass

    def stop(self):
        self._logger.info(
            f"Stopping receiver"
        )
        self._run = False
        if self._thread:
            self._thread.join()
