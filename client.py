import socket
import struct
import threading
import time
from typing import List, Tuple
import colorama
from colorama import Fore, Style

# Initialize colorama for cross-platform ANSI color support
colorama.init()

class SpeedTestClient:
    MAGIC_COOKIE = 0xabcddcba
    REQUEST_MSG_TYPE = 0x3
    
    def __init__(self):
        """Initialize the speed test client."""
        # Create UDP socket for receiving offers
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Use SO_REUSEADDR for Windows compatibility
        self.udp_socket.bind(('', 13117))
        
        print(f"{Fore.GREEN}Client started, listening for offer requests...{Style.RESET_ALL}")
    
    def get_user_parameters(self) -> Tuple[int, int, int]:
        """Get test parameters from user."""
        while True:
            try:
                file_size = int(input("Enter file size (bytes): "))
                tcp_connections = int(input("Enter number of TCP connections: "))
                udp_connections = int(input("Enter number of UDP connections: "))
                return file_size, tcp_connections, udp_connections
            except ValueError:
                print(f"{Fore.RED}Invalid input. Please enter numbers only.{Style.RESET_ALL}")
    
    def wait_for_server(self) -> Tuple[str, int, int]:
        """Wait for server offer message."""
        while True:
            try:
                data, addr = self.udp_socket.recvfrom(1024)
                
                # Parse offer message
                magic_cookie, msg_type, udp_port, tcp_port = struct.unpack('!IbHH', data)
                
                if magic_cookie == self.MAGIC_COOKIE and msg_type == 0x2:
                    print(f"{Fore.CYAN}Received offer from {addr[0]}{Style.RESET_ALL}")
                    return addr[0], udp_port, tcp_port
                
            except Exception as e:
                print(f"{Fore.RED}Error receiving offer: {str(e)}{Style.RESET_ALL}")
    
    def handle_tcp_transfer(self, server_ip: str, server_port: int, file_size: int, 
                          transfer_num: int) -> None:
        """Handle single TCP transfer."""
        try:
            # Create TCP connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((server_ip, server_port))
            
            # Send file size request
            sock.send(f"{file_size}\n".encode())
            
            # Receive data and measure time
            start_time = time.time()
            received = 0
            while received < file_size:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                received += len(chunk)
            
            # Calculate statistics
            total_time = time.time() - start_time
            speed = (received * 8) / total_time  # bits per second
            
            print(f"{Fore.GREEN}TCP transfer #{transfer_num} finished, "
                  f"total time: {total_time:.2f} seconds, "
                  f"total speed: {speed:.1f} bits/second{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}Error in TCP transfer #{transfer_num}: {str(e)}{Style.RESET_ALL}")
        finally:
            sock.close()
    
    def handle_udp_transfer(self, server_ip: str, server_port: int, file_size: int,
                          transfer_num: int) -> None:
        """Handle single UDP transfer."""
        try:
            # Create UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            # Send request
            request = struct.pack('!IbQ', self.MAGIC_COOKIE, self.REQUEST_MSG_TYPE, file_size)
            sock.sendto(request, (server_ip, server_port))
            
            # Receive data and measure time
            start_time = time.time()
            received_segments = set()
            total_segments = None
            last_receive_time = time.time()
            
            while True:
                try:
                    sock.settimeout(1.0)  # 1 second timeout
                    data, _ = sock.recvfrom(4096)
                    last_receive_time = time.time()
                    
                    # Parse payload header
                    header_size = struct.calcsize('!IbQQ')
                    magic_cookie, msg_type, total_segs, current_seg = struct.unpack(
                        '!IbQQ', data[:header_size]
                    )
                    
                    if magic_cookie != self.MAGIC_COOKIE or msg_type != 0x4:
                        continue
                    
                    total_segments = total_segs
                    received_segments.add(current_seg)
                    
                except socket.timeout:
                    if time.time() - last_receive_time >= 1.0:
                        break
            
            # Calculate statistics
            total_time = time.time() - start_time
            if total_segments:
                success_rate = (len(received_segments) / total_segments) * 100
                speed = (len(received_segments) * len(data[header_size:]) * 8) / total_time
                
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
        """Run the complete speed test following the state machine architecture."""
        # Initial setup - get parameters once at startup
        file_size, tcp_count, udp_count = self.get_user_parameters()
        
        while True:
            # State: Looking for server (Step 4)
            print(f"{Fore.GREEN}Client started, listening for offer requests...{Style.RESET_ALL}")
            
            # Wait for server (Step 5)
            server_ip, udp_port, tcp_port = self.wait_for_server()
            
            # State: Speed test
            threads: List[threading.Thread] = []
            
            # Create TCP transfer threads
            for i in range(tcp_count):
                thread = threading.Thread(
                    target=self.handle_tcp_transfer,
                    args=(server_ip, tcp_port, file_size, i + 1)
                )
                threads.append(thread)
            
            # Create UDP transfer threads
            for i in range(udp_count):
                thread = threading.Thread(
                    target=self.handle_udp_transfer,
                    args=(server_ip, udp_port, file_size, i + 1)
                )
                threads.append(thread)
            
            # Start all transfers
            for thread in threads:
                thread.start()
            
            # Wait for all transfers to complete
            for thread in threads:
                thread.join()
            
            # All transfers complete - print message and loop back to looking for server (Step 4)
            print(f"{Fore.GREEN}All transfers complete, listening to offer requests{Style.RESET_ALL}")

if __name__ == "__main__":
    client = SpeedTestClient()
    client.run_speed_test()