from ftplib import FTP
from dataclasses import dataclass

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
            print(e)

    def uploadFile(self, src_path, tgt_path):
        try:
            with FTP(self.tgt_address, self.username, self.password) as f:
                with open(src_path, "rb") as file:
                    f.storbinary(f"STOR {tgt_path}", file)
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