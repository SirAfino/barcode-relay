from datetime import datetime
import json
from device_reader import DeviceReader
import interception_py.interception as interception
import re
from keycodes import codeToChar

class InterceptionDeviceReader(DeviceReader):
    # Gets the device handle (integer) for the given HWID regex, return -1 if not found
    # This function is needed because, using the default interception class to get the handle
    # results in some issues that do not allow to get data from the device afterwards
    def get_device_handle(self):
        for i in range(interception.MAX_DEVICES):
            device = interception.device(
                interception.k32.CreateFileA(b'\\\\.\\interception%02d' % i, 0x80000000,0,0,3,0,0),
                interception.k32.CreateEventA(0, 1, 0, 0),
                interception.interception.is_keyboard(i)
            )
            hwid = device.get_HWID().decode("utf-16")
            if re.match(self._hwid_regex, hwid) is not None:
                return i

        return -1
    
    def device_filter(self, interception: interception.interception):
        def filter(device):
            return 1 if re.match(self._hwid_regex, interception.get_HWID(device)) else 0
        
        return filter

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
            new_handle = self.get_device_handle()
            if handle is None or new_handle != handle:
                handle = new_handle

                if handle == -1:
                    self._logger.info(
                        f"Device disconnected"
                    )
                else:
                    self._logger.info(
                        f"Device re/connected"
                    )
                
                    # Add a filter to capture data from the new device
                    c.set_filter(
                        self.device_filter(c),
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
            if type(stroke) is not interception.key_stroke:
                continue
            if stroke.state != interception.interception_key_state.INTERCEPTION_KEY_DOWN.value:
                continue
            
            buffer += codeToChar(stroke.code)

            # Check if the string is a full scan
            if re.match(self._full_scan_regex, buffer):
                ts = int(datetime.now().timestamp())
                self._queue.put((self._id, buffer, ts))
                self._logger.info(f"Read scan: {json.dumps({'code': buffer})}")
                buffer = ""
