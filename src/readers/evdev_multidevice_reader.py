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

from datetime import datetime
import json
from queue import Queue
import re
from time import sleep
from readers.evdev_device_reader import EvdevDeviceReader
from readers.multidevice_reader import MultiDeviceReader
from config import DeviceConfig

class EvdevMultiDeviceReader(MultiDeviceReader):
    """Multi device reader using the evdev (Linux)"""
    _readers: list[EvdevDeviceReader] = []

    def __init__(self, configs: DeviceConfig, queue: Queue, polling_ms: int = 500) -> None:
        super().__init__(configs, queue, polling_ms)

        # Create a single device evdev reader for each configuration
        for config in self._configs:
            self._readers.append(EvdevDeviceReader(config, queue, polling_ms))

    def run(self):
        # Keep a buffer of the device data
        buffers = ["" for _ in self._configs]

        while self._run:
            # Keep track of valid events,
            # if no valid event has occurred wait before looping again
            # otherwise loop again directly
            valid_events_count = 0

            for i, reader in enumerate(self._readers):
                if not reader.grab():
                    # If device is still not grabbed, wait and retry
                    continue

                raw_events = reader.read()
                if raw_events is None:
                    # If no events or device has disconnected wait and retry
                    continue

                for raw_event in raw_events:
                    event_char = reader.parse_event_as_char(raw_event)
                    if event_char is None:
                        continue

                    buffers[i] += event_char
                    valid_events_count += 1

                    # Check if the string is a full scan
                    if re.match(self._configs[i].full_scan_regex, buffers[i]):
                        ts = int(datetime.now().timestamp())
                        self._queue.put((self._configs[i].id, buffers[i], ts))
                        self._logger.info(
                            "Read scan: %s", json.dumps({'code': buffers[i]}),
                            extra={ 'component': f"READER:{self._configs[i].id}" }
                        )
                        buffers[i] = ""

            if valid_events_count == 0:
                sleep(self._polling_ms / 1000.0)
