# Bloomy Battery Simulator 1200 Python Driver
This package enables CAN communication to the Bloomy BS1200 through the PEAK Systems PCAN-USB FD adapter. 
To install, open a command line in the dist directory and use the command 'pip install BS1200_driver-1.0.0-py3-none-any.whl'
Package is compatible with Windows and Unix platforms
Requires Python version 3.6 or greater
## feature list

* Instantiate a CAN Bus supporting up to 16 Parallel BS1200 units

* HIL Mode Configuration
:   When in HIL mode, the Battery Simulator 1200 gives priority to the specified incoming frames to reduce latency; the instrument will attempt to pass non-HIL frames through for processing but delivery is not guaranteed. Before using, the CAN HIL Publishing Configuration must be set.

* Query BS1200 for board Temperatures and Fan Faults

* Individual Cell Control
     - Enable or Disable Cell
     - Set Cell Voltage
     - Readback Cell Voltage 
     - Set Cell Sinking and Sourcing Current Limits
     - Readback Cell Current 
     - Readback Cell Current 

* Enable/Disable all Cells
* Set all Cell Voltages
* Readback all Cell Voltages
* Set all Cell Sinking & Sourcing Limits
* Readback all Cell Currents
* Format strings for cell readbacks console printing

* Set Voltages for Analog Output Channels 1-2
* Readback Analog Input Channel
* Readback All Analog Input Channels
* Set direction and enable status for Digital Input/Output Channels 1-8
* Readback DIO Channels

### Upcoming/Planned Features
 * NI-XNET (CAN) USB adapter support
 * Ethernet (TCPIP/UDP) support 

## Use Instructions
Once the package has been installed to the python environment, it may be used to communicate action statuses with target BS1200 units, or to configure settings for a BS1200 at a designated IP address. 
### Driver

### ConfigTools
The features of the configuration mode seen in the BS1200 Soft Front Panel are available as a module of the b1200 python driver.
This module allows you to view and alter the Protocol, Ethernet, and CAN configurations for an individual BS1200 unit.
The configuration tools can be used with the following import statement
```
from bs1200 import ConfigTools
```
To apply individual categories can be used by importing the dataclasses used for each type of configuration
```
from bs1200 import ConfigTools, Ethernet_Settings, CAN_Settings, Protocol
```
By just importing the ConfigTools configuration settings may be read as a json object (optionally to a .json file) using get_all_settings(ExportToFile: bool) and apply_config_file(cfg_file_path: str).