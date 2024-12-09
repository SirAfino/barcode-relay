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

# from datetime import datetime
# import json
# import re

from datetime import datetime
import json
from queue import Queue
import re
from time import sleep
import evdev
import evdev.events

from device_config import DeviceConfig
from readers.keycodes import code_to_char
from .device_reader import DeviceReader

class EvdevDeviceReader(DeviceReader):
    """Device reader using the evdev (Linux)"""

    def __init__(self, config: DeviceConfig, queue: Queue, polling_ms: int = 500) -> None:
        super().__init__(config, queue, polling_ms)

    def run(self):
        # Keep a buffer of the device data
        buffer = ""

        # Keep a variable to check if device is
        # detected and events are grabbed
        device_grabbed = False

        while self._run:
            if not device_grabbed:
                try:
                    device = evdev.InputDevice(self._config.hwid_regex)
                    device.grab()

                    device_grabbed = True
                    buffer = ""

                    self._logger.info(
                        "Device re/connected",
                        extra={ 'component': 'READER' }
                    )
                except FileNotFoundError:
                    pass
                except PermissionError:
                    pass

                # If device is still not grabbed, wait and retry
                if not device_grabbed:
                    sleep(self._polling_ms / 1000.0)
                    continue

            # Try to read pending events from the device
            try:
                raw_events: list[evdev.events.InputEvent] = device.read()
                for raw_event in raw_events:
                    if not isinstance(raw_event, evdev.events.InputEvent):
                        self._logger.error(
                            "Received invalid event",
                            extra={ 'component': 'READER' }
                        )
                        continue

                    event = evdev.categorize(raw_event)
                    if not isinstance(event, evdev.events.KeyEvent):
                        # Not interested
                        continue

                    if event.keystate != evdev.events.KeyEvent.key_down:
                        # Not interested
                        continue

                    buffer += code_to_char(event.scancode)

                    # Check if the string is a full scan
                    if re.match(self._config.full_scan_regex, buffer):
                        ts = int(datetime.now().timestamp())
                        self._queue.put((self._config.id, buffer, ts))
                        self._logger.info(
                            "Read scan: %s", json.dumps({'code': buffer}),
                            extra={ 'component': f"READER:{self._config.id}" }
                        )
                        buffer = ""
            except BlockingIOError:
                # No pending event for this device, wait and retry
                sleep(self._polling_ms / 1000.0)
            except OSError:
                # Device has disconnected, wait and retry
                self._logger.info(
                    "Device disconnected",
                    extra={ 'component': 'READER' }
                )
                device_grabbed = False
                sleep(self._polling_ms / 1000.0)
                continue
