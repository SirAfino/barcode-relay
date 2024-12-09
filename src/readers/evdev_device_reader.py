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

from readers.keycodes import code_to_char
from config import DeviceConfig
from .device_reader import DeviceReader

class EvdevDeviceReader(DeviceReader):
    """Device reader using the evdev (Linux)"""

    # Keep track if device has been grabbed or not
    # (also keep track if the device disconnects)
    _grabbed = False

    # Keep a buffer of the device data
    _buffer = ""

    _device: evdev.InputDevice = None

    def __init__(self, config: DeviceConfig, queue: Queue, polling_ms: int = 500) -> None:
        super().__init__(config, queue, polling_ms)

    def grab(self):
        """
        If device is not already grabbed, try to get device handle and grab the device
        (make this software the only handler of his events).
        Return True if device has been grabbed (or already was), False otherwise.
        """
        if self._grabbed and self._device is not None:
            return True

        try:
            self._device = evdev.InputDevice(self._config.hwid_regex)
            self._device.grab()

            self._grabbed = True
            self._buffer = ""

            self._logger.info(
                "Device re/connected",
                extra={ 'component': f"READER:{self._config.id}" }
            )
            return True
        except FileNotFoundError:
            self._device = None
        except PermissionError:
            self._device = None

        return False

    def read(self):
        """
        Read and return the list of pending events for the device
        """
        if self._device is None:
            return None

        # Try to read pending events from the device
        try:
            events: list[evdev.events.InputEvent] = []
            raw_events: list[evdev.events.InputEvent] = self._device.read()
            for raw_event in raw_events:
                events.append(raw_event)
            return events
        except BlockingIOError:
            # No pending event for this device, wait and retry
            return None
        except OSError:
            # Device has disconnected, wait and retry
            self._logger.info(
                "Device disconnected",
                extra={ 'component': f"READER:{self._config.id}" }
            )
            self._grabbed = False
            return None

    def parse_event_as_char(self, raw_event: evdev.InputEvent):
        """
        Try to parse the InputEvent as a char. Only parse keydown events, ignore others.
        Returns the character represented by the keydown event or None for other events.
        """
        if not isinstance(raw_event, evdev.events.InputEvent):
            self._logger.error(
                "Received invalid event",
                extra={ 'component': f"READER:{self._config.id}" }
            )
            return None

        event = evdev.categorize(raw_event)
        if not isinstance(event, evdev.events.KeyEvent):
            # Not interested
            return None

        if event.keystate != evdev.events.KeyEvent.key_down:
            # Not interested
            return None

        return code_to_char(event.scancode)

    def run(self):
        while self._run:
            if not self.grab():
                # If device is still not grabbed, wait and retry
                sleep(self._polling_ms / 1000.0)
                continue

            raw_events = self.read()
            if raw_events is None:
                # If no events or device has disconnected wait and retry
                sleep(self._polling_ms / 1000.0)
                continue

            for raw_event in raw_events:
                event_char = self.parse_event_as_char(raw_event)
                if event_char is None:
                    continue

                self._buffer += event_char

                # Check if the string is a full scan
                if re.match(self._config.full_scan_regex, self._buffer):
                    ts = int(datetime.now().timestamp())
                    self._queue.put((self._config.id, self._buffer, ts))
                    self._logger.info(
                        "Read scan: %s", json.dumps({'code': self._buffer}),
                        extra={ 'component': f"READER:{self._config.id}" }
                    )
                    self._buffer = ""
