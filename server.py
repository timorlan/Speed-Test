# server.py
import socket
import struct
import time
import colorama
from colorama import Fore, Style

colorama.init()

class SpeedTestServer:
    MAGIC_COOKIE = 0xabcddcba
    OFFER_MSG_TYPE = 0x2
    
    def __init__(self):
        self.udp_port = self._get_available_port('udp')
        self.tcp_port = self._get_available_port('tcp')
        
        self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        self.ip_address = self._get_ip_address()
        print(f"{Fore.GREEN}Server started, listening on IP address {self.ip_address}{Style.RESET_ALL}")
    
    def _get_available_port(self, protocol):
        sock = socket.socket(
            socket.AF_INET, 
            socket.SOCK_DGRAM if protocol == 'udp' else socket.SOCK_STREAM
        )
        sock.bind(('', 0))
        port = sock.getsockname()[1]
        sock.close()
        return port
    
    def _get_ip_address(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip
    
    def broadcast_offers(self):
        while True:
            try:
                offer_message = struct.pack('!IbHH', 
                    self.MAGIC_COOKIE,
                    self.OFFER_MSG_TYPE,
                    self.udp_port,
                    self.tcp_port
                )
                self.broadcast_socket.sendto(offer_message, ('<broadcast>', 13117))
                time.sleep(1)
            except Exception as e:
                print(f"{Fore.RED}Error in broadcast: {str(e)}{Style.RESET_ALL}")
    
    def run(self):
        self.broadcast_offers()

if __name__ == "__main__":
    server = SpeedTestServer()
    server.run()