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

import logging
from typing import List, Optional
import yaml
from pydantic import BaseModel, ValidationError, Field

class DeviceConfig(BaseModel):
    """
    USB Input device configuration
    """

    id: str = Field(...)
    hwid_regex: Optional[str] = None
    vid: Optional[int] = None
    pid: Optional[int] = None
    full_scan_regex: str = Field(".*?\n")

class TargetConfig(BaseModel):
    """
    Generic - Output target configuration
    """

    type: str = Field("dummy", pattern="redis_stream|dummy")
    host: str = Field("127.0.0.1")
    port: int = Field(6379, ge=1, le=65535)
    username: str = Field("")
    password: str = Field("")
    stream: str = Field("")

class SyslogConfig(BaseModel):
    """
    Syslog logging configuration
    """

    level: str = Field("INFO", pattern="DEBUG|INFO|WARNING|ERROR|CRITICAL")
    server_host: str = Field("127.0.0.1")
    server_port: int = Field(514, ge=1, le=65535)
    log_host: str = Field("barcode-relay")

class LoggingConfig(BaseModel):
    """
    Console logging configuration
    """
    level: str = Field("INFO", pattern="DEBUG|INFO|WARNING|ERROR|CRITICAL")
    filepath: str = Field(None)
    syslog: Optional[SyslogConfig] = None

class AppConfig(BaseModel):
    """
    App configuration
    """

    id: str = Field("barcode-relay")
    devices: List[DeviceConfig]
    target: TargetConfig
    logging: Optional[LoggingConfig] = LoggingConfig()

def load_configuration(filepath: str):
    """Load working configuration from specified file"""
    try:
        with open(filepath, 'r', encoding="utf-8") as file:
            yaml_data = yaml.safe_load(file)

        config = AppConfig(**yaml_data)
        return config
    except FileNotFoundError:
        return None
    except ValidationError as e:
        logger = logging.getLogger()
        logger.error("Configuration validation failed.")
        print(e)
        return None
