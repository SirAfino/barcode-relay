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

from queue import Queue
from sys import exit
from _version import __version__
import logging
import argparse
import interception_util
import yaml
from interception_device_reader import InterceptionDeviceReader
from time import sleep
from sender import Sender

CONFIG_FILEPATH = "config.yml"
LOGS_FILEPATH = "app.log"

def licenseNotice() -> str:
    return (
        "BarcodeRelay  Copyright (C) 2024  Gabriele Serafino\n"+
        "This program comes with ABSOLUTELY NO WARRANTY.\n"+
        "This is free software, and you are welcome to redistribute it\n"+
        "under certain conditions."
    )

def loadConfiguration(filepath: str = CONFIG_FILEPATH):
    try:
        with open(filepath, 'r') as file:
            configuration = yaml.safe_load(file)
        return configuration
    except FileNotFoundError:
        return None

def setupLogger(level = logging.INFO, filepath: str = None):
    logger = logging.getLogger()
    logger.setLevel(level)
    
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s [%(component)s] [%(uuid)s] %(message)s',
        defaults={'component': 'APP', 'uuid': ''}
    )

    streamHandler = logging.StreamHandler()
    streamHandler.setLevel(level)
    streamHandler.setFormatter(formatter)
    logger.addHandler(streamHandler)

    if filepath is not None:
        fileHandler = logging.FileHandler(filepath)
        fileHandler.setLevel(level)
        fileHandler.setFormatter(formatter)
        logger.addHandler(fileHandler)

    return logger


def main():
    print(licenseNotice())
    print()

    # Parse command line arguments to check if the user just wants to list USB devices, otherwise
    # start the program normally
    argsParser = argparse.ArgumentParser()
    argsParser.add_argument("-l", "--list", action="store_true", help="List available USB devices HWID")
    args = argsParser.parse_args()

    if args.list:
        print("List of attached HID USB devices (Hardware ID):")
        devices = interception_util.listKeyboardDevices()
        for device in devices:
            print(f" - {device}")

        if len(devices) == 0:
            print("   No device found")
            
        print()
        exit(0)

    logger = setupLogger(logging.DEBUG, LOGS_FILEPATH)
    logger.info(f'BarcodeRelay - v{__version__}')

    config = loadConfiguration()
    if config is None:
        logger.error(f'Error while loading configuration file from "{CONFIG_FILEPATH}".')
        logger.error(f'Make sure the configuration file exists and conforms the provided configuration template.')
        exit(-1)

    logger.info("Configuration loaded")

    queue = Queue()

    device_reader = InterceptionDeviceReader(
        config['device']['hwid_regex'],
        config['device']['full_scan_regex'],
        queue
    )

    sender = Sender(queue)

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
