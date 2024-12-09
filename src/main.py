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
import logging.handlers
import argparse
from time import sleep
from queue import Queue
import sys
import json
from datetime import datetime
import os
from syslog_rfc5424_formatter import RFC5424Formatter
from _version import __version__
from config import LoggingConfig, load_configuration
from senders.sender import Sender

CONFIG_FILEPATH = "config/config.yml"
LOG_FORMATTER = logging.Formatter(
    '%(asctime)s %(levelname)s [%(component)s] %(message)s',
    defaults={'component': 'APP', 'uuid': ''}
)

def license_notice() -> str:
    """Print license notice text"""
    return (
        "BarcodeRelay  Copyright (C) 2024  Gabriele Serafino\n"+
        "This program comes with ABSOLUTELY NO WARRANTY.\n"+
        "This is free software, and you are welcome to redistribute it\n"+
        "under certain conditions."
    )

def setup_defualt_logger():
    """Setup default logger for before loading the configuration"""
    logger = logging.getLogger("default")
    logger.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(LOG_FORMATTER)
    logger.addHandler(stream_handler)

    return logger

def setup_logger(config: LoggingConfig):
    """Setup logger for console and file logging"""
    logger = logging.getLogger()
    logger.setLevel(config.level)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(config.level)
    stream_handler.setFormatter(LOG_FORMATTER)
    logger.addHandler(stream_handler)

    if config.filepath is not None:
        file_handler = logging.FileHandler(config.filepath)
        file_handler.setLevel(config.level)
        file_handler.setFormatter(LOG_FORMATTER)
        logger.addHandler(file_handler)

    if config.syslog:
        syslog_handler = logging.handlers.SysLogHandler(
            facility=logging.handlers.SysLogHandler.LOG_DAEMON,
            address=(config.syslog.server_host, config.syslog.server_port)
        )
        syslog_handler.setLevel(config.syslog.level)
        syslog_handler.setFormatter(RFC5424Formatter(
            'barcode_relay[%(component)s]: %(message)s'
        ))

        logger.addHandler(syslog_handler)

    return logger

def list_devices():
    """
    List attached USB keyboard devices
    """
    print("List of attached HID USB devices (Hardware ID):")

    #pylint: disable=import-outside-toplevel
    if os.name == "nt":
        import interception_util
        devices = interception_util.list_keyboard_devices()
    else:
        import evdev
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    #pylint: enable=import-outside-toplevel

    for device in devices:
        print(f" - {device}")

    if len(devices) == 0:
        print("   No device found")

    print()

def main():
    """Main function"""
    print(license_notice())
    print()

    # Parse command line arguments to check if the user just wants to list USB devices, otherwise
    # start the program normally
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument(
        "-l", "--list", action="store_true", help="List available USB devices HWID")
    args_parser.add_argument("-t", "--test", help="Test send a single code")
    args = args_parser.parse_args()

    if args.list:
        list_devices()
        sys.exit(0)

    logger = setup_defualt_logger()
    logger.info('BarcodeRelay - v%s', __version__)

    config = load_configuration(CONFIG_FILEPATH)
    if config is None:
        logger.error('Error while loading configuration file from "%s".', CONFIG_FILEPATH)
        logger.error('Make sure the configuration file exists \
                     and conforms the provided configuration template.')
        sys.exit(-1)

    logger.info("Configuration loaded")

    logger = setup_logger(config.logging)

    queue = Queue()

    if config.target.type == 'redis_stream':
        #pylint: disable=import-outside-toplevel
        from senders.redis_stream_sender import RedisStreamSender
        #pylint: enable=import-outside-toplevel
        sender = RedisStreamSender(
            config.id,
            queue,
            config.target.host,
            config.target.port,
            config.target.username,
            config.target.password,
            config.target.stream,
        )
    elif config.target.type == 'dummy':
        sender = Sender(config.id, queue)
    else:
        logger.error("Invalid target type %s, exiting", config.target.type)
        sys.exit(-1)

    if args.test:
        sender.start()
        ts = int(datetime.now().timestamp())
        queue.put((config.devices[0].id, args.test, ts))
        logger.info(
            "Simulate scan: %s", json.dumps({'code': args.test}),
            extra={ 'component': f"READER:{config.devices[0].id}" }
        )
        sleep(1)
        sender.stop()
        sys.exit(0)

    #pylint: disable=import-outside-toplevel
    if os.name == 'nt':
        from readers.interception_multidevice_reader import InterceptionMultiDeviceReader
        device_reader = InterceptionMultiDeviceReader(config.devices, queue)
    else:
        # from readers.multidevice_reader import MultiDeviceReader
        from readers.evdev_device_reader import EvdevDeviceReader
        device_reader = EvdevDeviceReader(config.devices[0], queue)
    #pylint: enable=import-outside-toplevel

    device_reader.start()
    sender.start()

    # Run loop
    run = True
    while run:
        try:
            sleep(1)
        except KeyboardInterrupt:
            run = False

    device_reader.stop()
    sender.stop()


if __name__ == "__main__":
    main()
