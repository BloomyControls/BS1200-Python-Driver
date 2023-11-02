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
## Installation
Install the package by saving the .whl file from the project releases page https://github.com/BloomyControls/BS1200-Python-Driver/releases/
Open command line, powershell, or another terminal to the location the .whl file was saved and run the following command to install using pip package manager
Windows:
```
pip install "\path\to\whl\file\BS1200_driver-X.X.X-py3-none-any.whl"
```
Linux:
```
pip3 install "/path/to/whl/file/BS1200_driver-X.X.X-py3-none-any.whl"
```
Alternative to downloading a release, the library may be built to the project /dist/ directory by running the command 
```
python -m build
```
from the same directory the project's pyproject.toml file is found, and install using pip from the freshly built .whl in the /dist/ directory.
## Use Instructions
Once the package has been installed to the python environment, the `BS1200` driver class may be used to communicate action statuses with target BS1200 units over a PCAN adapter, or to configure settings for a BS1200 at a designated IP address using the `ConfigTools` class. 
### BS1200 (driver)
To initialize the driver, simply create an instance with a integer list of the Box IDs of the BS1200 units connected to the PCAN bus, i.e.
```
from bs1200 import BS1200

test_unit = BS1200([1])
test_unit.query_system_status(1)
test_unit.close()
``` 
Or an equivalent statement using the Python 'with' structure can be used for the driver:
```
from bs1200 import BS1200

with BS1200([1]) as bs:
     bs.query_system_status(1)
```
for a single BS1200 with the CAN Box ID set to 1.
Once the object is created, the PCAN bus is initialized and a communication session using the device channel PCAN_USBBUS1 has started. The following action status methods may then be used to interact with the BS1200 bus:
| Driver Method Name    | Parameters                                                                                                                                                                                                                                                                | Description                                                                                                                                                                                                                                                                                                                                                                                                                             |
|-----------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| query_system_status   | boxid (int): Box ID of the queried unit                                                                                                                                                                                                                                   | Returns printed statements for the unit's fan statuses and temperature sensor readings                                                                                                                                                                                                                                                                                                                                                  |
| hil_mode              | boxid (int): Box ID of the target unitenable_HIL (bool): True to enable HIL Mode, False to disable                                                                                                                                                                        | Enable or disable the BS1200 in HIL mode. Returns PCAN bus OK status. Once set, the Battery Simulator will execute only the commands defined as active in HIL mode. By default all auxiliary configuration channels are set to disabled during HIL mode. In order to change this option, the configuration frame must be used. Note, the Configure frame is not supported in HIL mode, so this must be sent while HIL mode is disabled. |
| config_can_publishing | boxid (int): Target BS1200 unitdio_en (bool): Enable/Disable (True/False) digital IO publishing in HIL modeao_en (bool): Enable/Disable (True/False) analog publishing in HIL modeai_en (bool): Enable/Disable (True/False) analog output publishing in HIL mode          | Sends the configuration frame for CAN publishing in HIL Mode. The Configure frame is not supported in HIL mode, so this must be sent while HIL mode is disabled.                                                                                                                                                                                                                                                                        |
| cell_enable           | boxid (int): Target BS1200 unitchannel (int): BS1200 cell to change enabled status of                                                                                                                                                                                     | Enable or disable a cell channel on the target BS1200 unit. Enter 'true' to enable, 'false' to disable, valid channel values 1-12                                                                                                                                                                                                                                                                                                       |
| cell_enable_all       | boxid (int): Target BS1200 unit                                                                                                                                                                                                                                           | Enable or disable all channels for a target BS1200 unit. Enter 'true' to enable, 'false' to disable                                                                                                                                                                                                                                                                                                                                     |
| set_cell_V            | boxid (int): Target BS1200 unitchannel (int): Cell to set voltage forvoltage (float): voltage level to set the designated cell                                                                                                                                            | Set an individual cell (1-12) to designated voltage value input range 0.00 to 5.00 Volts                                                                                                                                                                                                                                                                                                                                                |
| set_V_all             | boxid (int): Target BS1200 unittgt_volt (float): Target voltage to set all cell channels                                                                                                                                                                                  | Set the cell voltage for Cells 1-12, valid inputs from 0.00 to 5.00 Volts                                                                                                                                                                                                                                                                                                                                                               |
| readback_cell_V       | boxid (int): Target BS1200 unitchannel (int): Cell to read voltage of                                                                                                                                                                                                     | Readback voltage value of designated cell channel 1-12, returns float value.                                                                                                                                                                                                                                                                                                                                                            |
| readback_V_all        | boxid (int): Target BS1200 unit                                                                                                                                                                                                                                           | Return list of voltage values (V) for all cell channels.                                                                                                                                                                                                                                                                                                                                                                                |
| set_cell_I_sink       | boxid (int): Target BS1200 unitchannel (int): Cell to set sinking current limit ofsink_current (float): Target cell current sinking limit (valid values 0-0.5A)                                                                                                           | Construct and send message to set an individual cell current sinking value                                                                                                                                                                                                                                                                                                                                                              |
| set_cell_I_source     | boxid (int): Target BS1200 unitchannel (int): Cell to set sourcing current limit ofsource_current (float): Target cell current sinking limit (valid values 0-0.5A)                                                                                                        | Construct and send message to set an individual cell current sourcing value                                                                                                                                                                                                                                                                                                                                                             |
| set_I_all             | boxid (int): Target BS1200 unitsink_i (float): Sinking current for all cells, Valid in range 0-0.5 Asource_i (float): Sourcing current for all cells, Valid in range 0-0.5 A                                                                                              | Set the sink and sourcing current limits for all cells. Valid in range 0-0.5 A                                                                                                                                                                                                                                                                                                                                                          |
| readback_cell_I       | boxid (int): Target BS1200 unitchannel (int): Target cell channel                                                                                                                                                                                                         | Return the current readback (A) for the designated cell channel (1-12)                                                                                                                                                                                                                                                                                                                                                                  |
| readback_I_all        | boxid (int): Target BS1200 unit                                                                                                                                                                                                                                           | Return current readbacks (A) for all cell channels 1-12 as a list of floats                                                                                                                                                                                                                                                                                                                                                             |
| readback_ai_v         | boxid (int): Target BS1200 unitchannel (int): Target analog input channel                                                                                                                                                                                                 | Returns the voltage level for the target Analog Input Channel (valid channels 1-8)                                                                                                                                                                                                                                                                                                                                                      |
| readback_ai_all       | boxid (int): Target BS1200 unit                                                                                                                                                                                                                                           | Returns the voltage levels for Analog Input Channels 1-8 as an array of float values                                                                                                                                                                                                                                                                                                                                                    |
| ao_set                | boxid (int): BS1200 unit to set analog outputs forAO1_Voltage (float): voltage setpoint for AO 1 (0-5V)AO2_Voltage (float): voltage setpoint for AO 2 (0-5V)                                                                                                              | Set the BS1200's Analog Output voltage setpoints. Valid range from 0-5 V.                                                                                                                                                                                                                                                                                                                                                               |
| dio_set               | dio_dir (list[int]): List of Boolean values designating direction of each DIO Channel.                                     Set 1 to configure as Output, 0 to configure as Input.dio_en (list[int]): Enables the DIO line when the direction is also set as output (True) | Set the direction of Digital IO Channels 1-8.                                                                                                                                                                                                                                                                                                                                                                                           |
| readback_dio          | boxid (int): Box ID of unit to read DIO from                                                                                                                                                                                                                              | Returns state of Digital Input/Output Lines as a list of booleans                                                                                                                                                                                                                                                                                                                                                                       |

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
BS1200 Configuration JSON object example:
```
{
    "Protocol": "CAN",
    "IP_Address": "192.168.1.100",
    "Ethernet_Settings": {
        "TCP_Cmd_Port": "12345",
        "TCP_Cmd_Interval_ms": "10",
        "UDP_Read_Port": "54321",
        "UDP_Read_Interval_ms": "5"
    },
    "CAN_Settings": {
        "Box_ID": 1,
        "Write_Period_ms": 5
    },
	"Enable_SafetyInterlock" : false
}
```
By default the methods used to set configuration values will restart the connected target using the NI System Configuration API. It is highly reccomended to restart the unit whenever updating values to prevent a desynchronization between the target IP address saved to class properties and currently used IP address of the device.
When restarting the target BS1200, the console will output status messages while the module waits for the `nisyscfg` restart method to return, signalling that the target is back online. The `ConfigTools` object will update to the newly set IP address so that further configuration may take place without needing to recreate the object. 
