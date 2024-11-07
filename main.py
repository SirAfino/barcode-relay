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
import yaml
from syslog_rfc5424_formatter import RFC5424Formatter
from _version import __version__
from device_config import DeviceConfig
from senders.sender import Sender

CONFIG_FILEPATH = "config.yml"
LOGS_FILEPATH = "app.log"

def license_notice() -> str:
    """Print license notice text"""
    return (
        "BarcodeRelay  Copyright (C) 2024  Gabriele Serafino\n"+
        "This program comes with ABSOLUTELY NO WARRANTY.\n"+
        "This is free software, and you are welcome to redistribute it\n"+
        "under certain conditions."
    )

def load_configuration(filepath: str = CONFIG_FILEPATH):
    """Load working configuration from specified file"""
    try:
        with open(filepath, 'r', encoding="utf-8") as file:
            configuration = yaml.safe_load(file)
        return configuration
    except FileNotFoundError:
        return None

def setup_logger(level = logging.INFO, filepath: str = None):
    """Setup logger for console and file logging"""
    logger = logging.getLogger()
    logger.setLevel(level)

    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s [%(component)s] %(message)s',
        defaults={'component': 'APP', 'uuid': ''}
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if filepath is not None:
        file_handler = logging.FileHandler(filepath)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


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
        print("List of attached HID USB devices (Hardware ID):")
        if os.name == "nt":
            import interception_util
            devices = interception_util.list_keyboard_devices()
        else:
            # TODO: implement for linux
            devices = []

        for device in devices:
            print(f" - {device}")

        if len(devices) == 0:
            print("   No device found")

        print()
        sys.exit(0)

    logger = setup_logger(logging.DEBUG, LOGS_FILEPATH)
    logger.info('BarcodeRelay - v%s', __version__)

    config = load_configuration()
    if config is None:
        logger.error('Error while loading configuration file from "%s".', CONFIG_FILEPATH)
        logger.error('Make sure the configuration file exists \
                     and conforms the provided configuration template.')
        sys.exit(-1)

    logger.info("Configuration loaded")

    # Setup syslog if configured
    if config['syslog']:
        syslog_handler = logging.handlers.SysLogHandler(
            facility=logging.handlers.SysLogHandler.LOG_DAEMON,
            address=(config['syslog']['server_host'], config['syslog']['server_port'])
        )
        syslog_handler.setLevel(logging.DEBUG)
        syslog_handler.setFormatter(RFC5424Formatter(
            'barcode_relay[%(component)s]: %(message)s'
        ))
        logger.addHandler(syslog_handler)

    queue = Queue()

    device_configs = []
    for c in config['devices']:
        device_configs.append(DeviceConfig(
            c['id'],
            c['hwid_regex'],
            c['full_scan_regex']
        ))

    if config['target']['type'] == 'redis_stream':
        #pylint: disable=import-outside-toplevel
        from senders.redis_stream_sender import RedisStreamSender
        #pylint: enable=import-outside-toplevel
        sender = RedisStreamSender(
            config['id'],
            queue,
            config['target']['host'],
            config['target']['port'],
            config['target']['username'],
            config['target']['password'],
            config['target']['stream'],
        )
    elif config['target']['type'] == 'dummy':
        sender = Sender(config['id'], queue)
    else:
        logger.error("Invalid target type %s, exiting", config['target']['type'])
        sys.exit(-1)

    if args.test:
        sender.start()
        ts = int(datetime.now().timestamp())
        queue.put((config['devices'][0]['id'], args.test, ts))
        logger.info(
            "Simulate scan: %s", json.dumps({'code': args.test}),
            extra={ 'component': f"READER:{config['devices'][0]['id']}" }
        )
        sleep(1)
        sender.stop()
        sys.exit(0)

    #pylint: disable=import-outside-toplevel
    if os.name == 'nt':
        from readers.interception_multidevice_reader import InterceptionMultiDeviceReader
        device_reader = InterceptionMultiDeviceReader(device_configs, queue)
    else:
        from readers.multidevice_reader import MultiDeviceReader
        device_reader = MultiDeviceReader(device_configs, queue)
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
