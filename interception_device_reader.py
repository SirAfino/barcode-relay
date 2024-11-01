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
import re
from device_reader import DeviceReader
from interception_py import interception
from interception_util import get_device_handle, regex_device_filter
from keycodes import code_to_char

class InterceptionDeviceReader(DeviceReader):
    """Device reader using the interception driver (Windows only)"""

    def run(self):
        # Instantiate the interception object
        c = interception.interception()

        # Track the current device handle, needed to check if the device was
        # disconnected and reconnected again
        handle = None

        # Keep a buffer of the device data
        buffer = ""

        while self._run:
            # Get the current device handle and check if its different from
            # the one we had on the previous cycle
            new_handle = get_device_handle(self._config.hwid_regex)
            if handle is None or new_handle != handle:
                handle = new_handle

                if handle == -1:
                    self._logger.info(
                        "Device disconnected",
                        extra={ 'component': 'READER' }
                    )
                else:
                    self._logger.info(
                        "Device re/connected",
                        extra={ 'component': 'READER' }
                    )

                    # Add a filter to capture data from the new device
                    c.set_filter(
                        regex_device_filter(c, [self._config.hwid_regex]),
                        interception.interception_filter_key_state.INTERCEPTION_FILTER_KEY_ALL.value
                    )

            # Try to get data from the intercepted device
            device = c.wait(self._polling_ms)
            if device < 0:
                # No data, poll again
                continue

            stroke = c.receive(device)

            # Every event is intercepted from the target device, only interesting
            # one is the KEY_DOWN event
            if not isinstance(stroke, interception.key_stroke):
                continue
            if stroke.state != interception.interception_key_state.INTERCEPTION_KEY_DOWN.value:
                continue

            buffer += code_to_char(stroke.code)

            # Check if the string is a full scan
            if re.match(self._config.full_scan_regex, buffer):
                ts = int(datetime.now().timestamp())
                self._queue.put((self._config.id, buffer, ts))
                self._logger.info(
                    "Read scan: %s", json.dumps({'code': buffer}),
                    extra={ 'component': f"READER:{self._config.id}" }
                )
                buffer = ""
