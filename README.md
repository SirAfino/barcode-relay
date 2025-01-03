# BarcodeRelay
Captures data from USB Barcode Scanner(s) (or any keyboard-like device) and sends them over the internet to an external messaging queue.

## Dependencies
This software makes use of **interception** (https://github.com/oblitum/Interception) and **interception_py** (https://github.com/cobrce/interception_py).

Before using this software, the **interception** driver must be installed.
You can follow instructions on the official repository on GitHub.

For convenience, the driver installer is included in this repo (as *interception/install-interception.exe*). Run install-interception without any arguments inside an console executed as administrator and it will give instructions for installation.

**interception_py** is a port of the interception dll in python. The relevant code used by this project has been placed in the *interception_py* folder. You can check out its info and license in the readme (*interception/README.md* and *interception/LICENSE*) or in the official repository on GitHub.

## Usage

### Find the desired USB device hardware ID
Executing the program with the *--list* flag, it will output the list of USB devices detected as keyboards, for each device a string representing its hardware id (HWID) is printed.

To identify which device is the desired one, you can run the program with the *--list* flag twice, once before and once after attaching the USB device, and checking which hwid was not present before. 

### Run the program
*TODO*

## Build .exe
pyinstaller --noconfirm --onedir --console --icon "assets/barcode.ico" --hidden-import "ctypes"  --name "BarcodeRelay" "src/main.py"