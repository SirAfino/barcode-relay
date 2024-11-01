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
from interception_py import interception
from interception_util import get_device_handle, regex_device_filter
from keycodes import code_to_char
from multidevice_reader import MultiDeviceReader

class InterceptionMultiDeviceReader(MultiDeviceReader):
    def device_handle_to_device_index(self, _interception: interception.interception, handle: int):
        for i, config in enumerate(self._configs):
            if re.match(config.hwid_regex, _interception.get_HWID(handle)):
                return i

        return -1

    def run(self):
        # Instantiate the interception object
        c = interception.interception()

        # Track the current device handle, needed to check if the device was
        # disconnected and reconnected again
        handles = [None for _ in self._configs]

        # Keep a buffer of the device data
        buffers = ["" for _ in self._configs]

        while self._run:
            for i, config in enumerate(self._configs):
                # Get the current device handle and check if its different from
                # the one we had on the previous cycle
                new_handle = get_device_handle(config.hwid_regex)
                if not (handles[i] is None or new_handle != handles[i]):
                    continue

                handles[i] = new_handle

                if handles[i] == -1:
                    self._logger.info(
                        "Device disconnected",
                        extra={ 'component': f"READER:{config.id}" }
                    )
                else:
                    self._logger.info(
                        "Device re/connected",
                        extra={ 'component': f"READER:{config.id}" }
                    )

                    # Add a filter to capture data from the new device
                    c.set_filter(
                        regex_device_filter(c, [conf.hwid_regex for conf in self._configs]),
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

            index = self.device_handle_to_device_index(c, device)
            if index < 0:
                continue

            buffers[index] += code_to_char(stroke.code)

            # Check if the string is a full scan
            if re.match(self._configs[index].full_scan_regex, buffers[index]):
                ts = int(datetime.now().timestamp())
                self._queue.put((self._configs[index].id, buffers[index], ts))
                self._logger.info(
                    "Read scan: %s", json.dumps({'code': buffers[index]}),
                    extra={ 'component': f"READER:{self._configs[index].id}" }
                )
                buffers[index] = ""
