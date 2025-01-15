import socket
import struct
import threading
import time
import random
from typing import Tuple
import signal
import colorama
from colorama import Fore, Style
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
colorama.init()

class SpeedTestServer:
    TEAM_NAME = "ByteBusters"
    MAGIC_COOKIE = 0xabcddcba
    OFFER_MSG_TYPE = 0x2
    PAYLOAD_MSG_TYPE = 0x4
    SEGMENT_SIZE = 1024

    def __init__(self):
        try:
            self.udp_port = self._get_available_port('udp')
            self.tcp_port = self._get_available_port('tcp')
        except Exception as e:
            print(f"{Fore.RED}Failed to initialize ports: {str(e)}{Style.RESET_ALL}")
            raise


        self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)

        self.ip_address = self._get_ip_address()
        print(f"{Fore.CYAN}Team {self.TEAM_NAME} - Server started, listening on IP address {self.ip_address}, TCP Port {self.tcp_port}, UDP Port {self.udp_port}{Style.RESET_ALL}")
        
        self.running = True
        signal.signal(signal.SIGINT, self.stop)

    def stop(self, signum, frame):
        print(f"{Fore.RED}Shutting down the server gracefully...{Style.RESET_ALL}")
        self.running = False

    def _get_available_port(self, protocol: str) -> int:
        """Retrieve an available port for the given protocol."""
        sock = socket.socket(
            socket.AF_INET, 
            socket.SOCK_DGRAM if protocol == 'udp' else socket.SOCK_STREAM
        )
        sock.bind(('', 0))
        port = sock.getsockname()[1]
        sock.close()
        return port

    
    def _get_ip_address(self) -> str:
        """Determine the server's local IP address."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip


    def get_broadcast_address(self):
        try:
            temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            temp_socket.connect(("8.8.8.8", 80))
            local_ip = temp_socket.getsockname()[0]
            temp_socket.close()

            ip_parts = local_ip.split('.')
            ip_parts[-1] = '255'
            broadcast_ip = '.'.join(ip_parts)

            return broadcast_ip

        except Exception as e:
            print(f"Error finding broadcast address: {e}")
            return None


    def broadcast_offers(self):
        """Continuously broadcast offer messages to clients."""
        while self.running:
            try:
                offer_message = struct.pack('!IbHH', 
                    self.MAGIC_COOKIE,
                    self.OFFER_MSG_TYPE,
                    self.udp_port,
                    self.tcp_port
                )
                broadcast_ip = self.get_broadcast_address()
                if broadcast_ip:
                    self.broadcast_socket.sendto(offer_message, (broadcast_ip, 13117))
                time.sleep(1)
            except Exception as e:
                print(f"{Fore.RED}Error in broadcast: {str(e)}{Style.RESET_ALL}")

    def handle_tcp_client(self, client_socket: socket.socket, addr: Tuple[str, int]):
        """Handle incoming TCP client requests."""
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

            print(f"{Fore.GREEN}TCP transfer completed for {addr}, total bytes sent: {bytes_sent}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error handling TCP client: {str(e)}{Style.RESET_ALL}")
        finally:
            client_socket.close()

    def handle_udp_client(self, data: bytes, addr: Tuple[str, int]) -> None:
        """Handle incoming UDP client requests."""
        try:
            print(f"{Fore.CYAN}New UDP request from {addr}{Style.RESET_ALL}")
            magic_cookie, msg_type, file_size = struct.unpack('!IbQ', data)

            if magic_cookie != self.MAGIC_COOKIE or msg_type != 0x3:
                print(f"{Fore.YELLOW}Invalid UDP request from {addr}{Style.RESET_ALL}")
                return

            total_segments = (file_size + self.SEGMENT_SIZE - 1) // self.SEGMENT_SIZE
            segments = [
                struct.pack('!IbQQ', self.MAGIC_COOKIE, self.PAYLOAD_MSG_TYPE, total_segments, i) +
                bytearray(random.getrandbits(8) for _ in range(self.SEGMENT_SIZE))
                for i in range(total_segments)
            ]

            send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            for segment in segments:
                if random.random() > 0.05:  # Simulate 5% packet loss
                    send_socket.sendto(segment, addr)
                time.sleep(0.001)

            print(f"{Fore.GREEN}UDP transfer completed for {addr}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error handling UDP client: {str(e)}{Style.RESET_ALL}")
        finally:
            send_socket.close()  # Explicitly close the socket


    def run(self):
        """Start the server's main execution loop."""
        print_banner()
        broadcast_thread = threading.Thread(target=self.broadcast_offers, daemon=True)
        broadcast_thread.start()

        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.bind(('', self.tcp_port))
        tcp_socket.listen(5)

        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind(('', self.udp_port))

        while self.running:
            try:
                tcp_socket.setblocking(False)
                udp_socket.setblocking(False)

                try:
                    client_socket, addr = tcp_socket.accept()
                    threading.Thread(target=self.handle_tcp_client, args=(client_socket, addr)).start()
                except BlockingIOError:
                    # Non-blocking mode might throw this; continue without crashing
                    pass
                except Exception as e:
                    print(f"{Fore.RED}Error accepting TCP connection: {str(e)}{Style.RESET_ALL}")


                try:
                    data, addr = udp_socket.recvfrom(1024)
                    threading.Thread(target=self.handle_udp_client, args=(data, addr)).start()
                except BlockingIOError:
                    pass

                time.sleep(0.01)
            except Exception as e:
                print(f"{Fore.RED}Error in main loop: {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    server = SpeedTestServer()
    server.run()
