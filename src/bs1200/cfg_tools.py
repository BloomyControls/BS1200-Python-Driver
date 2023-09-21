from ftplib import FTP
from dataclasses import dataclass
from paramiko import SSHClient
from scp import SCPClient

class FtpHelper(object):
    """
    Class used to wrap FTP file download and upload processes in methods
    """
    def __init__(self, tgt: str, user: str, password : str):
        self.tgt_address = tgt
        self.username = user
        self.password = password

    def getFile(self, tgt_path, dest_path) -> str:
        try:
            with FTP(self.tgt_address, self.username, self.password) as f:
                with open(dest_path, "wb") as file:
                    # Command for Downloading the file "RETR filename"
                    retr = f.retrbinary(f"RETR {tgt_path}", file.write)
            return dest_path
        except Exception as e:
            raise e

    def uploadFile(self, src_path, tgt_path):
        try:
            with FTP(self.tgt_address, self.username, self.password) as f:
                with open(src_path, "rb") as file:
                    f.storbinary(f"STOR {tgt_path}", file)
        except Exception as e:
            raise e

class ScpHelper(object):
    """
    Class used to wrap SSH and SCP file transfer for sbRIO 9603 controllers. Call using 'with' statements, or call open
    """
    def __init__(self, tgt: str, user: str, password : str):
        self.tgt_address = tgt
        self.username = user
        self.password = password

    def __enter__(self):
        try:
            self.open()
        except Exception as e:
            print(e)

    def __exit__(self):
        self.close()

    def open(self):
        """Open """
        self.ssh = SSHClient()
        self.ssh.load_system_host_keys()
        self.ssh.connect(self.tgt_address)
        # SCPCLient takes a paramiko transport as an argument
        self.scp = SCPClient(self.ssh.get_transport())

    def close(self):
        """Close SCP and SSH connections"""
        self.scp.close()
        self.ssh.close()
    
    def getFile(self, tgt_path, dest_path) -> str:
        try:
            with self.scp as s:
                s.get(remote_path=tgt_path, local_path=dest_path)
            return dest_path
        except Exception as e:
            print(e)

    def uploadFile(self, src_path, tgt_path):
        try:
            with self.scp as s:
                s.put(files=src_path, remote_path=tgt_path)
        except Exception as e:
            print(e)


@dataclass
class Ethernet_Settings:
    IP_Address : str
    Command_Port : int
    Command_Interval_ms : int
    Reporting_Port : int
    Reporting_Interval_ms : int

@dataclass
class CAN_Settings:
    box_id : int
    publish_period_us : int

@dataclass
class Protocol:
    CAN = 0
    Ethernet = 1