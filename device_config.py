class DeviceConfig:
    id: str
    hwid_regex: str
    full_scan_regex: str

    def __init__(self, id: str, hwid_regex: str, full_scan_regex: str) -> None:
        self.id = id
        self.hwid_regex = hwid_regex
        self.full_scan_regex = full_scan_regex
