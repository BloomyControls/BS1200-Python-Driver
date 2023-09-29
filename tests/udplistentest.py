import socket
import time
import struct
import sys
import os
def listen_udp(ip, port, read_interval_ms):
    # Create a UDP socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Bind the socket to the specified IP and port
    udp_socket.bind((ip, port))
    # Set the socket timeout to the read interval in seconds
    udp_socket.settimeout(read_interval_ms / 1000.0)
    print(f"Listening on {ip}:{port} with a timeout of {read_interval_ms} ms")
    run = True
    clr = '\033[A'
    while run:
        try:
            # Receive data from the socket
            data = udp_socket.recv(1024)
            # Print received data and sender's address
            #print(f"Received from {addr}:\n{data}")
            print(f"rx size: {len(data)} bytes")
            prints = "";
            for i in range(0, 10):
                start = int(i*18)
                end = start + 18
                frame = data[start:end]
                
                arb, ext, type = struct.unpack(">I?B", frame[0:6])        
                payload = struct.unpack("8s", frame[10:18])
                prints += (#f"bytes {start}:{end}\tlength: {len(frame)}\t{frame}\n"+
                f"arb_id: {arb}\text: {ext}\ttype: {type}\tdata: {payload}\n")

            os.system('cls')
            print(f"\r{prints}", end='\r')
            time.sleep(1)
        except socket.timeout:
            # Handle the timeout here (no data received within the timeout)
            print("Timeout: No data received")
            run = False
        except KeyboardInterrupt:
            print("Stopping UDP listener...")
            run = False
    # Close the socket when done
    udp_socket.close()        
if __name__ == "__main__":
    ip = ""  # Change to your desired IP address
    port = 54321    # Change to your desired port number
    read_interval_ms = 5*1.2  # Change to your desired read interval in milliseconds
    
    listen_udp(ip, port, read_interval_ms)
