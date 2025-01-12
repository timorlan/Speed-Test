import socket
import struct
import threading
import time
from typing import List, Tuple
import colorama
from colorama import Fore, Style

colorama.init()

class SpeedTestClient:
    MAGIC_COOKIE = 0xabcddcba
    REQUEST_MSG_TYPE = 0x3
    
    def __init__(self):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Handle platform differences for socket options
        if hasattr(socket, 'SO_REUSEPORT'):  # Unix/Linux systems
            self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        else:  # Windows systems
            self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)
        self.udp_socket.bind(('', 13117))
    
    def get_user_parameters(self) -> Tuple[int, int, int]:
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
    
    def wait_for_server(self) -> Tuple[str, int, int]:
        while True:
            try:
                data, addr = self.udp_socket.recvfrom(1024)
                magic_cookie, msg_type, udp_port, tcp_port = struct.unpack('!IbHH', data)
                
                if magic_cookie == self.MAGIC_COOKIE and msg_type == 0x2:
                    print(f"{Fore.CYAN}Received offer from {addr[0]}{Style.RESET_ALL}")
                    return addr[0], udp_port, tcp_port
                
            except Exception as e:
                print(f"{Fore.RED}Error receiving offer: {str(e)}{Style.RESET_ALL}")
    
    def handle_tcp_transfer(self, server_ip: str, server_port: int, file_size: int, 
                          transfer_num: int) -> None:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((server_ip, server_port))
            
            sock.send(f"{file_size}\n".encode())
            
            start_time = time.time()
            received = 0
            while received < file_size:
                chunk = sock.recv(8192)
                if not chunk:
                    break
                received += len(chunk)
            
            total_time = time.time() - start_time
            speed = (received * 8) / total_time
            
            print(f"{Fore.GREEN}TCP transfer #{transfer_num} finished, "
                  f"total time: {total_time:.2f} seconds, "
                  f"total speed: {speed:.1f} bits/second{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}Error in TCP transfer #{transfer_num}: {str(e)}{Style.RESET_ALL}")
        finally:
            sock.close()
    
    def handle_udp_transfer(self, server_ip: str, server_port: int, file_size: int,
                          transfer_num: int) -> None:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)
            sock.settimeout(0.05)
            
            request = struct.pack('!IbQ', self.MAGIC_COOKIE, self.REQUEST_MSG_TYPE, file_size)
            sock.sendto(request, (server_ip, server_port))
            
            start_time = time.time()
            total_segments = (file_size + 1024 - 1) // 1024
            received_segments = {}
            last_receive_time = time.time()
            received_bytes = 0
            
            while True:
                try:
                    data, _ = sock.recvfrom(2048)
                    last_receive_time = time.time()
                    
                    header_size = struct.calcsize('!IbQQ')
                    magic_cookie, msg_type, total_segs, current_seg = struct.unpack(
                        '!IbQQ', data[:header_size]
                    )
                    
                    if magic_cookie != self.MAGIC_COOKIE or msg_type != 0x4:
                        continue
                    
                    if current_seg not in received_segments:
                        received_segments[current_seg] = len(data) - header_size
                        received_bytes += len(data) - header_size
                    
                    if len(received_segments) >= total_segs or (
                        time.time() - last_receive_time >= 0.5 and
                        time.time() - start_time >= 1.0
                    ):
                        break
                        
                except socket.timeout:
                    if time.time() - last_receive_time >= 0.5 and received_segments:
                        break
            
            total_time = time.time() - start_time
            success_rate = (len(received_segments) / total_segments) * 100
            speed = (received_bytes * 8) / total_time
            
            print(f"{Fore.GREEN}UDP transfer #{transfer_num} finished, "
                  f"total time: {total_time:.2f} seconds, "
                  f"total speed: {speed:.1f} bits/second, "
                  f"percentage of packets received successfully: {success_rate:.1f}%"
                  f"{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}Error in UDP transfer #{transfer_num}: {str(e)}{Style.RESET_ALL}")
        finally:
            sock.close()
    
    def run_speed_test(self):
        file_size, tcp_count, udp_count = self.get_user_parameters()
        
        while True:
            print(f"{Fore.CYAN}Team {self.TEAM_NAME} - Client started, listening for offer requests...{Style.RESET_ALL}")
            
            server_ip, udp_port, tcp_port = self.wait_for_server()
            
            threads: List[threading.Thread] = []
            
            for i in range(tcp_count):
                thread = threading.Thread(
                    target=self.handle_tcp_transfer,
                    args=(server_ip, tcp_port, file_size, i + 1)
                )
                threads.append(thread)
            
            for i in range(udp_count):
                thread = threading.Thread(
                    target=self.handle_udp_transfer,
                    args=(server_ip, udp_port, file_size, i + 1)
                )
                threads.append(thread)
            
            for thread in threads:
                thread.start()
            
            for thread in threads:
                thread.join()
            
            print(f"{Fore.GREEN}All transfers complete, listening to offer requests{Style.RESET_ALL}")

    def analyze_transfer_stats(self, transfer_times, transfer_speeds):
        """Calculate and display aggregate statistics for transfers"""
        avg_time = sum(transfer_times) / len(transfer_times)
        avg_speed = sum(transfer_speeds) / len(transfer_speeds)
        min_speed = min(transfer_speeds)
        max_speed = max(transfer_speeds)
        print(f"{Fore.CYAN}Aggregate Statistics:")
        print(f"Average transfer time: {avg_time:.2f} seconds")
        print(f"Average speed: {avg_speed:.1f} bits/second")
        print(f"Min speed: {min_speed:.1f} bits/second")
        print(f"Max speed: {max_speed:.1f} bits/second{Style.RESET_ALL}")
        return avg_time, avg_speed, min_speed, max_speed

    def reconnect_on_failure(self, sock, server_ip, server_port, max_attempts=3):
        """Implement retry logic for failed connections"""
        for attempt in range(max_attempts):
            try:
                sock.connect((server_ip, server_port))
                return True
            except Exception as e:
                print(f"{Fore.YELLOW}Connection attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_attempts - 1:
                    print(f"{Fore.RED}Maximum reconnection attempts reached{Style.RESET_ALL}")
                    return False
                time.sleep(1)
        return False

    def monitor_network_conditions(self, start_time, received_bytes, total_bytes):
        """Track network conditions during transfer"""
        current_time = time.time()
        elapsed_time = current_time - start_time
        if elapsed_time > 0:
            current_speed = (received_bytes * 8) / elapsed_time
            progress = (received_bytes / total_bytes) * 100
            print(f"{Fore.CYAN}Progress: {progress:.1f}% - Current Speed: {current_speed:.1f} bits/second{Style.RESET_ALL}")
        return current_speed if elapsed_time > 0 else 0

if __name__ == "__main__":
    client = SpeedTestClient()
    client.run_speed_test()