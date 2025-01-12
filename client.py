# client.py
import socket
import struct
import colorama
from colorama import Fore, Style

colorama.init()

class SpeedTestClient:
    MAGIC_COOKIE = 0xabcddcba
    REQUEST_MSG_TYPE = 0x3
    
    def __init__(self):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if hasattr(socket, 'SO_REUSEPORT'):
            self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        else:
            self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.bind(('', 13117))
    
    def get_user_parameters(self):
        while True:
            try:
                file_size = int(input("Enter file size (bytes): "))
                tcp_connections = int(input("Enter number of TCP connections: "))
                udp_connections = int(input("Enter number of UDP connections: "))
                if file_size <= 0 or tcp_connections <= 0 or udp_connections <= 0:
                    raise ValueError("Values must be positive")
                return file_size, tcp_connections, udp_connections
            except ValueError as e:
                print(f"{Fore.RED}Invalid input: {str(e)}. Please enter positive numbers only.{Style.RESET_ALL}")
    
    def wait_for_server(self):
        while True:
            try:
                data, addr = self.udp_socket.recvfrom(1024)
                magic_cookie, msg_type, udp_port, tcp_port = struct.unpack('!IbHH', data)
                
                if magic_cookie == self.MAGIC_COOKIE and msg_type == 0x2:
                    print(f"{Fore.CYAN}Received offer from {addr[0]}{Style.RESET_ALL}")
                    return addr[0], udp_port, tcp_port
                
            except Exception as e:
                print(f"{Fore.RED}Error receiving offer: {str(e)}{Style.RESET_ALL}")
    
    def run_speed_test(self):
        print(f"{Fore.GREEN}Client started, listening for offer requests...{Style.RESET_ALL}")
        file_size, tcp_count, udp_count = self.get_user_parameters()
        server_ip, udp_port, tcp_port = self.wait_for_server()
        
if __name__ == "__main__":
    client = SpeedTestClient()
    client.run_speed_test()