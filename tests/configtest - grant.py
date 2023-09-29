import sys
import json
sys.path.append('src')
from bs1200 import ConfigTools, Ethernet_Settings, CAN_Settings, Protocol

test = ConfigTools('[BS1200_IP_HERE]', 'admin', '')
print(test.get_all_settings(False))
test.apply_config_file('bs1200_cfg.json', False)


