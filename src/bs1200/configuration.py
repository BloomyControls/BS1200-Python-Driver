import os
import sys
import time
import nisyscfg
from configparser import ConfigParser
import xml.etree.ElementTree as ET
from bs1200.cfg_tools import *
import json
import threading

class ConfigTools(object):

    def __init__(self, tgt_address, username= "admin", password= ""):
        """
        tgt_address: str, 
        username: str = "admin", 
        password: str = ""
        """
        self.ip_address = tgt_address
        self.user = username
        self.pwd = password
        self.FTP = FtpHelper(tgt_address, username, password)
        self.SCP = ScpHelper(tgt_address, username, password)
        self.ini_parser = ConfigParser()
        self.__9603 = False

    def retrieve_file(self, tgt_file: str, dest: str):
        if(self.__9603):
            #fix the path to ni-rt.ini if  ni-rt linux is target
            if("ni-rt.ini" in tgt_file):
                    tgt_file = "/etc/natinst/share/ni-rt.ini"
            local_copy = self.SCP.get_file(tgt_file, dest)
        else:
            #Try the FTP, if this fails to connect use SCP
            try:
                local_copy = self.FTP.get_file(tgt_file, dest)
            except:
                #if error from FTP, use SCP via SSH 
                print("Could not connect to target via FTP, using SCP")
                self.__9603 = True
                if("ni-rt.ini" in tgt_file):
                    tgt_file = "/etc/natinst/share/ni-rt.ini"
                local_copy = self.SCP.get_file(tgt_file, dest)
        
        return local_copy
        

    def send_file(self, tgt, dest_path):
        if(self.__9603):
            #fix the path to ni-rt.ini if  ni-rt linux is target
                if("ni-rt.ini" in dest_path):
                    dest_path = "/etc/natinst/share/ni-rt.ini"
                self.SCP.upload_file(tgt, dest_path)
        else:
            #Try the FTP, if this fails to connect use SCP
            try:
                self.FTP.upload_file(tgt, dest_path)
            except:
                #if error from FTP, use SCP via SSH 
                self.__9603 = True
                #fix the path to ni-rt.ini if  ni-rt linux is target
                if("ni-rt.ini" in dest_path):
                    dest_path = "/etc/natinst/share/ni-rt.ini"
                self.SCP.upload_file(tgt, dest_path)

    def apply_config_file(self, cfg_file_path, restart: bool = True):
        """
        Takes in a .json file with BS1200 configuration object in the 
        following format and applies the parsed settings. 
        By default the target device is restarted after applying
        configuration changes.
        BS1200_Configuration:
        {
            "Protocol" : "CAN",
            "IP_Address" : "192.168.1.103",
            "Ethernet_Settings" : 
            {
                "TCP_Cmd_Port"      : 12345,
                "TCP_Cmd_Interval_ms"  : 10,
                "UDP_Read_Port"     : 54321,
                "UDP_Read_Interval_ms" : 5 
            },
            "CAN_Settings": 
            {
                "Box_ID"            : 1,
                "Write_Period_ms"   : 5
            },
	        "Enable_SafetyInterlock" : true
        }
        """
        with open(cfg_file_path) as json_file:
            config = json.load(json_file)

        mode =  (Protocol.CAN if (config["Protocol"] == "CAN") 
                 else Protocol.Ethernet)
        can_cfg = CAN_Settings(config["CAN_Settings"]["Box_ID"], 
            int(config["CAN_Settings"]["Write_Period_ms"]*1000))
        
        eth_cfg = Ethernet_Settings(config["IP_Address"], 
            config["Ethernet_Settings"]['TCP_Cmd_Port'], 
            config["Ethernet_Settings"]['TCP_Cmd_Interval_ms'], 
            config["Ethernet_Settings"]['UDP_Read_Port'], 
            config["Ethernet_Settings"]['UDP_Read_Interval_ms'])
        en_interlock = config["Enable_SafetyInterlock"]
        #print(mode)       
        #print(can_cfg)
        #print(eth_cfg)

        self.apply_general_settings(mode, False)
        self.enable_safety_interlock(en_interlock, False)
        self.apply_can_config(can_cfg, False)
        self.apply_ethernet_settings(eth_cfg, False)
        if restart:
            self.__restart_unit()

    def get_all_settings(self, export_to_file: bool,
                               file_name: str = "bs1200_cfg.json") -> str:
        """
        Returns a prettyified JSON string of the BS1200 configuration values,
        optionally exporting to a generated bs1200_cfg.json file at the 
        path the method is executed from.
        """
        ethernet = self.get_ethernet_settings()
        can = self.get_can_settings()
        mode = self.get_protocol()
        interlock = self.interlock_enabled()
        config = {
            'Protocol' : mode, 
            'IP_Address' : ethernet.IP_Address,
            'Ethernet_Settings':
            {
                'TCP_Cmd_Port'      : ethernet.Command_Port,
                'TCP_Cmd_Interval_ms'  : ethernet.Command_Interval_ms,
                'UDP_Read_Port'     : ethernet.Reporting_Port,
                'UDP_Read_Interval_ms' : ethernet.Reporting_Interval_ms 
            },
            'CAN_Settings': 
            {
                'Box_ID'            : can.box_id,
                'Write_Period_ms'   : int(can.publish_period_us/1000)
            },
            'Enable_SafetyInterlock' : interlock
        }
        if export_to_file:
            with open(file_name, 'w') as f:
                f.write(json.dumps(config, indent=4))
        return json.dumps(config)
        
    def apply_general_settings(self, protocol: Protocol, restart: bool = True):
        """
        Sets the protocol used by the target BS1200 unit
        Valid values for protocol are Protocol.CAN or Protocol.Ethernet
        """
        rt_path = "/ni-rt/startup/Configuration Files/General Settings.xml"
        temp_path =  "General Settings.xml"
        
        cfgfile_path = self.retrieve_file(rt_path, temp_path)
        #build an XML tree for the xml file 
        ET.register_namespace("", "http://www.ni.com/LVData") 
        tree = ET.parse(cfgfile_path)
        #Replace The Protocol Choice
        for item in tree.iter():
            if 'EW' in item.tag:
                for child in item:
                    if 'Val' in child.tag:
                        child.text = str(protocol)
        #Rewrite the temp config file
        tree.write(cfgfile_path, encoding="utf-8", 
                   xml_declaration=True, 
                   short_empty_elements=False)
        #replace the configuration file on the target
        self.__replace_xml_declaration(cfgfile_path)
        self.send_file(cfgfile_path, rt_path)
        
        os.remove(temp_path)
        #restart unit by default
        if restart: 
            self.__restart_unit()

    def apply_ethernet_settings(self, tcpip_cfg: Ethernet_Settings, 
                                restart: bool = True):
        """
        Applies the provided TCP and UDP ethernet stack settings, 
        and updates the IP address of the target BS1200 unit
        """
        #update the TCP Settings file
        self.set_tcp_settings(tcpip_cfg.IP_Address,
                              tcpip_cfg.Command_Port, 
                              tcpip_cfg.Command_Interval_ms)
        #update the UDP Settings file
        self.set_udp_settings(tcpip_cfg.Reporting_Port, 
                              tcpip_cfg.Reporting_Interval_ms)
        #update the configured IP Address
        self.set_ip_address(tcpip_cfg.IP_Address)
        #restart if requested
        if restart:
            self.__restart_unit()
        
    def apply_can_config(self, can_cfg: CAN_Settings, restart: bool = True):
        """
        Applies the provided CAN Settings to the startup configuration, 
        settings a new Box ID and Publish Period (ms) for the BS1200 unit  
        """
        rt_path = "/ni-rt/startup/Data/BS1200 Configuration.ini"
        temp_path =  "BS1200 Configuration.ini"
        cfgfile_path = self.retrieve_file(rt_path, temp_path)
        self.__fix_XML_tags(cfgfile_path)
        #build an XML tree for the .ini file 🤦‍♂️ 
        tree = ET.parse(cfgfile_path)
        root = tree.getroot()
        #Replace Box ID
        root[0][3].text = str(can_cfg.box_id)
        #Replace Publish Period
        root[0][4].text = str(can_cfg.publish_period_us)
        #Rewrite the temp config file
        tree.write(cfgfile_path, encoding="utf-8", 
                   xml_declaration=True, 
                   short_empty_elements=False)
        #replace the configuration file on the target
        self.__replace_xml_declaration(cfgfile_path)
        self.send_file(cfgfile_path, rt_path)
        os.remove(temp_path)
        #restart unit by default
        if restart: 
            self.__restart_unit()

    def enable_safety_interlock(self, interlock, restart: bool = True):
        """
        Enables or disables the BS1200 Safety Interlock feature
        """
        rt_path = "/ni-rt/startup/Data/BS1200 Configuration.ini"
        temp_path =  "BS1200 Configuration.ini"
        cfgfile_path = self.retrieve_file(rt_path, temp_path)
        self.__fix_XML_tags(cfgfile_path)
        #build an XML tree for the .ini file 🤦‍♂️ 
        tree = ET.parse(cfgfile_path)
        root = tree.getroot()
        #Replace Enable_Cell_Inhibit
        root[3].text = "TRUE" if interlock else "FALSE"
        #Rewrite the temp config file
        tree.write(cfgfile_path, encoding="utf-8", 
                   xml_declaration=True, 
                   short_empty_elements=False)
        #replace the configuration file on the target
        self.__replace_xml_declaration(cfgfile_path)
        self.send_file(cfgfile_path, rt_path)
        os.remove(temp_path)
        #restart unit by default
        if restart: 
            self.__restart_unit()

    def set_ip_address(self, new_ip_address: str):
        """
        Sets a new IP Address for the target BS1200, restarting the unit 
        and updating the ip address used by the ConfigTools for further 
        configuration method calls
        """
        #no broadcast bytes allowed
        if("255" in new_ip_address):
            raise ValueError("Broadcast bytes are not allowed for the unit IP address")
        #get the ni-rt.ini file from the BS1200 controller root directory
        self.retrieve_file('ni-rt.ini', 'ni-rt.ini')
        #open the local copy of the cfg file and set the IP Address parameter of the
        #TCP_STACK_CONFIG section
        self.ini_parser.read('ni-rt.ini')
        try:
            self.ini_parser['TCP_STACK_CONFIG']['IP_Address'] = new_ip_address
        except:
            self.ini_parser['eth0']['IP_Address'] = new_ip_address
        #Rewrite the local copy of the ini file
        with open('ni-rt.ini', 'w') as file:
            self.ini_parser.write(file)
        #Send the file back to the target BS1200, replacing the entire file
        self.send_file('ni-rt.ini', 'ni-rt.ini')
        #remove local copy of cfg file
        os.remove('ni-rt.ini')

        #dont update this until we restart the unit with nisyscfg
        #self.FTP.tgt_address = self.ip_address = new_ip_address

    def set_tcp_settings(self, ip_address : str, 
                         cmd_port: int, cmd_interval_ms: int):
        """
        Update the TCP related settings in the Ethernet configuration
        """
        rt_path = "/ni-rt/startup/Configuration Files/TCP Settings.xml"
        temp_path =  "TCP Settings.xml"
        cfgfile_path = self.retrieve_file(rt_path, temp_path)
        #build an XML tree for the xml file 
        ET.register_namespace("", "http://www.ni.com/LVData") 
        tree = ET.parse(cfgfile_path)
        #replace the IP address value
        iterator = tree.iter()
        for item in iterator:
            if(item.text == 'IP Address'):
                next(iterator).text = ip_address
        #Replace The Port and Loop Time ms element values
        iterator = tree.iter()
        for item in iterator:
            if(item.text == 'Port'):
                next(iterator).text = str(cmd_port)
        #reset the iterator
        iterator = tree.iter()
        for item in iterator:
            if(item.text == 'Loop Time ms'):
                next(iterator).text = str(cmd_interval_ms)
        #Rewrite the temp config file
        tree.write(cfgfile_path, encoding="utf-8", 
                   xml_declaration=True, 
                   short_empty_elements=False)
        self.__replace_xml_declaration(cfgfile_path)
        #replace the configuration file on the target
        self.send_file(cfgfile_path, rt_path)
        os.remove(temp_path)

    def set_udp_settings(self, rep_port: int, rep_interval_ms: int):
        """
        Update the UDP related settings in the Ethernet configuration
        """
        rt_path = "/ni-rt/startup/Configuration Files/UDP Settings.xml"
        temp_path =  "UDP Settings.xml"
        cfgfile_path = self.retrieve_file(rt_path, temp_path)
        #build an XML tree for the xml file 
        ET.register_namespace("", "http://www.ni.com/LVData") 
        tree = ET.parse(cfgfile_path)
        #Replace The Port and Loop Delay RT ms element values
        iterator = tree.iter()
        for item in iterator:
            if(item.text == 'Port'):
                next(iterator).text = str(rep_port)
        #reset the iterator
        iterator = tree.iter()
        for item in iterator:
            if(item.text == 'Loop Delay RT ms'):
                next(iterator).text = str(rep_interval_ms)
        #Rewrite the temp config file
        tree.write(cfgfile_path, encoding="utf-8", 
                   xml_declaration=True, 
                   short_empty_elements=False)
        self.__replace_xml_declaration(cfgfile_path)
        #replace the configuration file on the target
        self.send_file(cfgfile_path, rt_path)
        os.remove(temp_path)
    
    def get_can_settings(self):
        """
        Retreive the can settings from the target BS1200
        """
        rt_path = "/ni-rt/startup/Data/BS1200 Configuration.ini"
        temp_path =  "BS1200 Configuration.ini"
        cfgfile_path = self.retrieve_file(rt_path, temp_path)
        self.__fix_XML_tags(cfgfile_path)
        #build an XML tree for the .ini file 🤦‍♂️ 
        tree = ET.parse(cfgfile_path)
        root = tree.getroot()
        os.remove(temp_path)
        return CAN_Settings(int(root[0][3].text),  int(root[0][4].text))
    
    def get_ethernet_settings(self):
        """
        Retreive the ethernet settings and IP address from the target device
        """
        ini_cfg = self.retrieve_file('ni-rt.ini', 'ni-rt.ini')
        #open the local copy of the cfg file and set the IP Address parameter
        #of the #TCP_STACK_CONFIG or eth0 section
        self.ini_parser.read(ini_cfg)
        try:
            ip = self.ini_parser['TCP_STACK_CONFIG']['IP_Address'].strip('"')
        except:
            ip = self.ini_parser['eth0']['IP_Address'].strip('"')
            
        tcp_path = "/ni-rt/startup/Configuration Files/TCP Settings.xml"
        udp_path = "/ni-rt/startup/Configuration Files/UDP Settings.xml"
        temp_path1 =  "TCP Settings.xml"
        temp_path2 =  "UDP Settings.xml"

        tcp_cfgfile_path = self.retrieve_file(tcp_path, temp_path1)
        udp_cfgfile_path = self.retrieve_file(udp_path, temp_path2)
        #build an XML tree for the xml file 
        ET.register_namespace("", "http://www.ni.com/LVData") 
        tcp_tree = ET.parse(tcp_cfgfile_path)
        #get tcp settings from xml
        iterator = tcp_tree.iter()
        for item in iterator:
            if(item.text == 'Port'):
                tcp_port = next(iterator).text
        iterator = tcp_tree.iter()
        for item in iterator:
            if(item.text == 'Loop Time ms'):
                tcp_interval = next(iterator).text
                
        udp_tree = ET.parse(udp_cfgfile_path)
        #Replace The Port and Loop Delay RT ms element values
        iterator = udp_tree.iter()
        for item in iterator:
            if(item.text == 'Port'):
                udp_port = next(iterator).text
        #reset the iterator
        iterator = udp_tree.iter()
        for item in iterator:
            if(item.text == 'Loop Delay RT ms'):
                udp_interval = next(iterator).text
        os.remove(temp_path1)
        os.remove(temp_path2)
        os.remove('ni-rt.ini')
        return Ethernet_Settings(ip, tcp_port, tcp_interval, udp_port, udp_interval)
    
    def interlock_enabled(self):
        """
        Retreive the state of the Safety Interlock from the target BS1200
        """
        rt_path = "/ni-rt/startup/Data/BS1200 Configuration.ini"
        temp_path =  "BS1200 Configuration.ini"
        cfgfile_path = self.retrieve_file(rt_path, temp_path)
        self.__fix_XML_tags(cfgfile_path)
        #build an XML tree for the .ini file 🤦‍♂️ 
        tree = ET.parse(cfgfile_path)
        root = tree.getroot()
        os.remove(temp_path)
        return True if root[3].text == "TRUE" else False

    def get_protocol(self):
        """
        Get the procotol form the general settings
        """
        rt_path = "/ni-rt/startup/Configuration Files/General Settings.xml"
        temp_path =  "General Settings.xml"
        cfgfile_path = self.retrieve_file(rt_path, temp_path)
        #build an XML tree for the xml file 
        ET.register_namespace("", "http://www.ni.com/LVData") 
        tree = ET.parse(cfgfile_path)
        #Replace The Protocol Choice
        for item in tree.iter():
            if 'EW' in item.tag:
                for child in item:
                    if 'Val' in child.tag:
                        mode = child.text
        os.remove(cfgfile_path)
        return "CAN" if mode =='0' else "Ethernet"
    
    def __restart_unit(self):
        """
        Use nisyscfg library to restart the target unit
        """
        #need to close SCP helper before restarting so socket isnt force closed
        if(self.__9603):
            #print("Closing SCP connection")
            self.SCP.close() 
        #open a nisyscfg session to the BS1200 to restart it
        with nisyscfg.Session(self.ip_address, self.user, self.pwd) as s:      
            #updates IP address for the ConfigTools instance to the new IP address once restart complete
            try: 
                ev = self.__start_anim(f"Restarting BS1200 ({self.ip_address})... ")
                self.ip_address = s.restart(timeout=60*5)
            except:
                print("Issue while restarting unit")
            finally:
                ev.set()
            #do this again just in case
            self.FTP.tgt_address = self.ip_address
            sys.stdout.flush()
            print("\r\n"+f"BS1200 at {self.ip_address} is back online")
            sys.stdout.flush()
            print("\n")
        if(self.__9603):
            #print("Reopening SCP connection")
            self.SCP.open()

    def __animate(self, loadingtext: str):
        """Animation loop for the restart wait"""
        idx = 0
        animation = "|/-\\"
        for idx in range(0,len(animation)):
            sys.stdout.write("\r"+loadingtext+animation[idx % len(animation)])
            sys.stdout.flush()
            idx += 1
            time.sleep(0.1)

    def __start_anim(self, text):
        """Starts threaded event looping the animation"""
        ev = threading.Event()
        def _loop(ev, text):
            while not ev.is_set():
                self.__animate(text)
        threading.Thread(target=_loop, args=(ev, text)).start()
        return ev

    def __fix_XML_tags(self, xml_file):
        """BS1200 units sometimes have duplicate opening tag for root in XML, 
        need to remove that for elementree"""
        lines = []
        with open(xml_file) as f:
            lines = f.readlines()
            if lines[1] == lines[2]:
                lines.remove(lines[1])
        with open(xml_file, 'w') as f:
            f.writelines(lines)

    def __replace_xml_declaration(self, xml_file):
        """
        Replace the first line of the XML file with the original xml declaration 
        (elementtree does not support the standalone parameter)
        """
        with open(xml_file) as file:
            lines = file.readlines()
            lines[0] = "<?xml version='1.0' standalone='yes' ?>\n"
        newlines = []
        for line in lines:
            if("LVData" not in line):
                newlines.append(line.replace('"', "'"))
            else:
                newlines.append(line)
        with open(xml_file, 'w') as file:
            file.writelines(newlines)
