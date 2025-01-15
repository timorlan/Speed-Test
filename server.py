# server.py
import socket
import struct
import threading
import time
import random
from typing import Tuple
import colorama
from colorama import Fore, Style

colorama.init()
def print_banner():
    banner = f"""
    {Fore.CYAN}
    ╔══════════════════════════════════════════════════════════╗
    ║  ____        _       ____             _                  ║
    ║ | __ ) _   _| |_ ___|  _ \ _   _ ___| |_ ___ _ __ ___  ║
    ║ |  _ \| | | | __/ _ \ |_) | | | / __| __/ _ \ '__/ __| ║
    ║ | |_) | |_| | ||  __/  _ <| |_| \__ \ ||  __/ |  \__ \ ║
    ║ |____/ \__, |\__\___|_| \_\__,_|___/\__\___|_|  |___/ ║
    ║        |___/                                            ║
    ║                Speed Test Server v1.0                   ║
    ╚══════════════════════════════════════════════════════════╝
    {Style.RESET_ALL}"""
    print(banner)

class SpeedTestServer:
    TEAM_NAME = "ByteBusters"
    MAGIC_COOKIE = 0xabcddcba
    OFFER_MSG_TYPE = 0x2
    PAYLOAD_MSG_TYPE = 0x4
    SEGMENT_SIZE = 1024
    
    def __init__(self):
        self.udp_port = self._get_available_port('udp')
        self.tcp_port = self._get_available_port('tcp')
        
        self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)
        
        self.ip_address = self._get_ip_address()
        print(f"{Fore.CYAN}Team {self.TEAM_NAME} - Server started, listening on IP address {self.ip_address}{Style.RESET_ALL}")    
    
    def _get_available_port(self, protocol: str) -> int:
        sock = socket.socket(
            socket.AF_INET, 
            socket.SOCK_DGRAM if protocol == 'udp' else socket.SOCK_STREAM
        )
        sock.bind(('', 0))
        port = sock.getsockname()[1]
        sock.close()
        return port
    
    def _get_ip_address(self) -> str:
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
    
    def handle_tcp_client(self, client_socket: socket.socket, addr: Tuple[str, int]):
        try:
            print(f"{Fore.CYAN}New TCP connection from {addr}{Style.RESET_ALL}")
            file_size_str = client_socket.recv(1024).decode().strip()
            file_size = int(file_size_str)
            
            bytes_sent = 0
            chunk_size = 8192
            
            while bytes_sent < file_size:
                remaining = file_size - bytes_sent
                current_chunk = min(chunk_size, remaining)
                data = bytearray(random.getrandbits(8) for _ in range(current_chunk))
                client_socket.sendall(data)
                bytes_sent += current_chunk
                
        except Exception as e:
            print(f"{Fore.RED}Error handling TCP client: {str(e)}{Style.RESET_ALL}")
        finally:
            client_socket.close()
    
    def handle_udp_client(self, data: bytes, addr: Tuple[str, int]):
        try:
            print(f"{Fore.CYAN}New UDP request from {addr}{Style.RESET_ALL}")
            
            magic_cookie, msg_type, file_size = struct.unpack('!IbQ', data)
            if magic_cookie != self.MAGIC_COOKIE or msg_type != 0x3:
                return
                
            total_segments = (file_size + self.SEGMENT_SIZE - 1) // self.SEGMENT_SIZE
            
            send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4 * 1024 * 1024)
            
            try:
                # Prepare all segments first
                segments = []
                for segment_num in range(total_segments):
                    remaining = file_size - (segment_num * self.SEGMENT_SIZE)
                    current_segment_size = min(self.SEGMENT_SIZE, remaining)
                    payload = bytearray(random.getrandbits(8) for _ in range(current_segment_size))
                    header = struct.pack('!IbQQ', 
                        self.MAGIC_COOKIE,
                        self.PAYLOAD_MSG_TYPE,
                        total_segments,
                        segment_num
                    )
                    segments.append(header + payload)
                
                # Send segments in bursts
                burst_size = 32
                for i in range(0, total_segments, burst_size):
                    for j in range(i, min(i + burst_size, total_segments)):
                        send_socket.sendto(segments[j], addr)
                    
            finally:
                send_socket.close()
                
        except Exception as e:
            print(f"{Fore.RED}Error handling UDP client: {str(e)}{Style.RESET_ALL}")
                
        except Exception as e:
            print(f"{Fore.RED}Error handling UDP client: {str(e)}{Style.RESET_ALL}")
    
    def run(self):
        print_banner()
        broadcast_thread = threading.Thread(target=self.broadcast_offers, daemon=True)
        broadcast_thread.start()
        
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.bind(('', self.tcp_port))
        tcp_socket.listen(5)
        
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind(('', self.udp_port))
        
        while True:
            try:
                tcp_socket.setblocking(False)
                try:
                    client_socket, addr = tcp_socket.accept()
                    thread = threading.Thread(
                        target=self.handle_tcp_client,
                        args=(client_socket, addr)
                    )
                    thread.start()
                except BlockingIOError:
                    pass
                
                udp_socket.setblocking(False)
                try:
                    data, addr = udp_socket.recvfrom(1024)
                    thread = threading.Thread(
                        target=self.handle_udp_client,
                        args=(data, addr)
                    )
                    thread.start()
                except BlockingIOError:
                    pass
                
                time.sleep(0.01)
                
            except Exception as e:
                print(f"{Fore.RED}Error in main loop: {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    server = SpeedTestServer()
    server.run()
