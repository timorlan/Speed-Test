import socket
import struct
import threading
import time
import random
from typing import Tuple
import colorama
from colorama import Fore, Style

# Initialize colorama for cross-platform ANSI color support
colorama.init()

class SpeedTestServer:
    MAGIC_COOKIE = 0xabcddcba
    OFFER_MSG_TYPE = 0x2
    PAYLOAD_MSG_TYPE = 0x4
    
    def __init__(self):
        """Initialize the speed test server with configuration and socket setup."""
        # Bind to random available ports for both TCP and UDP
        self.udp_port = self._get_available_port('udp')
        self.tcp_port = self._get_available_port('tcp')
        
        # Create UDP socket for broadcasting offers
        self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        # Get server IP address
        self.ip_address = self._get_ip_address()
        print(f"{Fore.GREEN}Server started, listening on IP address {self.ip_address}{Style.RESET_ALL}")
    
    def _get_available_port(self, protocol: str) -> int:
        """Get an available port for the specified protocol."""
        sock = socket.socket(
            socket.AF_INET, 
            socket.SOCK_DGRAM if protocol == 'udp' else socket.SOCK_STREAM
        )
        sock.bind(('', 0))
        port = sock.getsockname()[1]
        sock.close()
        return port
    
    def _get_ip_address(self) -> str:
        """Get the server's IP address."""
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
        """Continuously broadcast offer messages."""
        while True:
            try:
                # Create offer message
                offer_message = struct.pack('!IbHH', 
                    self.MAGIC_COOKIE,
                    self.OFFER_MSG_TYPE,
                    self.udp_port,
                    self.tcp_port
                )
                
                # Broadcast the offer
                self.broadcast_socket.sendto(offer_message, ('<broadcast>', 13117))
                time.sleep(1)
            except Exception as e:
                print(f"{Fore.RED}Error in broadcast: {str(e)}{Style.RESET_ALL}")
    
    def handle_tcp_client(self, client_socket: socket.socket):
        """Handle TCP client connection and file transfer."""
        try:
            # Receive file size request
            file_size_str = client_socket.recv(1024).decode().strip()
            file_size = int(file_size_str)
            
            # Generate and send random data
            data = bytearray(random.getrandbits(8) for _ in range(file_size))
            client_socket.sendall(data)
            
        except Exception as e:
            print(f"{Fore.RED}Error handling TCP client: {str(e)}{Style.RESET_ALL}")
        finally:
            client_socket.close()
    
    def handle_udp_client(self, data: bytes, addr: Tuple[str, int]):
        """Handle UDP client request and file transfer."""
        try:
            # Parse request message
            magic_cookie, msg_type, file_size = struct.unpack('!IbQ', data)
            
            if magic_cookie != self.MAGIC_COOKIE or msg_type != 0x3:
                return
            
            # Calculate number of segments
            segment_size = 1024  # Adjust based on your needs
            total_segments = (file_size + segment_size - 1) // segment_size
            
            # Send data in segments
            for segment_num in range(total_segments):
                remaining = file_size - (segment_num * segment_size)
                current_segment_size = min(segment_size, remaining)
                
                # Create payload data
                payload = bytearray(random.getrandbits(8) for _ in range(current_segment_size))
                
                # Create payload message
                header = struct.pack('!IbQQ', 
                    self.MAGIC_COOKIE,
                    self.PAYLOAD_MSG_TYPE,
                    total_segments,
                    segment_num
                )
                
                # Send message
                self.broadcast_socket.sendto(header + payload, addr)
                time.sleep(0.001)  # Small delay to prevent overwhelming the network
                
        except Exception as e:
            print(f"{Fore.RED}Error handling UDP client: {str(e)}{Style.RESET_ALL}")
    
    def run(self):
        """Start the server and handle incoming connections."""
        # Start broadcast thread
        broadcast_thread = threading.Thread(target=self.broadcast_offers, daemon=True)
        broadcast_thread.start()
        
        # Set up TCP listener
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.bind(('', self.tcp_port))
        tcp_socket.listen(5)
        
        # Set up UDP listener
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind(('', self.udp_port))
        
        while True:
            try:
                # Non-blocking TCP accept
                tcp_socket.setblocking(False)
                try:
                    client_socket, addr = tcp_socket.accept()
                    print(f"{Fore.CYAN}New TCP connection from {addr}{Style.RESET_ALL}")
                    thread = threading.Thread(
                        target=self.handle_tcp_client,
                        args=(client_socket,)
                    )
                    thread.start()
                except BlockingIOError:
                    pass
                
                # Non-blocking UDP receive
                udp_socket.setblocking(False)
                try:
                    data, addr = udp_socket.recvfrom(1024)
                    print(f"{Fore.CYAN}New UDP request from {addr}{Style.RESET_ALL}")
                    thread = threading.Thread(
                        target=self.handle_udp_client,
                        args=(data, addr)
                    )
                    thread.start()
                except BlockingIOError:
                    pass
                
                time.sleep(0.01)  # Small delay to prevent busy waiting
                
            except Exception as e:
                print(f"{Fore.RED}Error in main loop: {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    server = SpeedTestServer()
    server.run()