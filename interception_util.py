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

import re
from ctypes import windll
from interception_py import interception

def list_keyboard_devices() -> list[str]:
    """Returns a list of attached USB keyboard devices"""

    k32 = windll.LoadLibrary('kernel32')

    hwids = []

    for i in range(interception.MAX_DEVICES):
        is_keyboard = interception.interception.is_keyboard(i)

        if not is_keyboard:
            continue

        device = interception.device(
            k32.CreateFileA(b'\\\\.\\interception%02d' % i, 0x80000000,0,0,3,0,0),
            k32.CreateEventA(0, 1, 0, 0),
            is_keyboard
        )
        hwid = device.get_HWID().decode("utf-16")

        if len(hwid) > 0:
            hwids.append(hwid)

    return hwids

def regex_device_filter(_interception: interception.interception, regexs: list[str]):
    """Returns a filter function that filters by multiple hwid regular expressions"""
    def _filter(device):
        for regex in regexs:
            if re.match(regex, _interception.get_HWID(device)):
                return 1

        return 0

    return _filter

def get_device_handle(regex: str):
    """Returns the device id for this USB device"""
    for i in range(interception.MAX_DEVICES):
        device = interception.device(
            interception.k32.CreateFileA(b'\\\\.\\interception%02d' % i, 0x80000000,0,0,3,0,0),
            interception.k32.CreateEventA(0, 1, 0, 0),
            interception.interception.is_keyboard(i)
        )
        hwid = device.get_HWID().decode("utf-16")
        if re.match(regex, hwid) is not None:
            return i

    return -1
