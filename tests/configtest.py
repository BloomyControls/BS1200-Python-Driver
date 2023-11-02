import sys
import json
sys.path.append('src')
from bs1200 import ConfigTools, Ethernet_Settings, CAN_Settings, Protocol

test = ConfigTools('127.0.0.1', 'FtpUser', 'LocalAdmin!')
print(test.get_all_settings(False))
with open('bs1200_cfg.json', 'w') as f:
    json.dump({"Protocol": "CAN", "IP_Address": "192.168.1.102", "Ethernet_Settings": 
    {"TCP_Cmd_Port": "12345", "TCP_Cmd_Interval_ms": "20", "UDP_Read_Port": "54321", "UDP_Read_Interval_ms": "10"}, 
    "CAN_Settings": {"Box_ID": 2, "Write_Period_ms": 5}, "Enable_SafetyInterlock" : False}, f)

test.apply_config_file('bs1200_cfg.json', False)


