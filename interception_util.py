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

from ctypes import *
from interception_py import interception

k32 = windll.LoadLibrary('kernel32')

def listKeyboardDevices() -> list[str]:
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
