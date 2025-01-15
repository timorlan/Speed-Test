import socket
import struct
import threading
import time
from typing import List, Tuple
import signal
import colorama
from colorama import Fore, Style
def print_banner():
    banner = f"""
    {Fore.CYAN}
    ╔══════════════════════════════════════════════════════════╗
    ║  ____        _       ____             _                  ║
    ║ | __ ) _   _| |_ ___|  _ \ _   _ ___| |_ ___ _ __ ___    ║
    ║ |  _ \| | | | __/ _ \ |_) | | | / __| __/ _ \ '__/ __|   ║
    ║ | |_) | |_| | ||  __/  _ <| |_| \__ \ ||  __/ |  \__ \   ║
    ║ |____/ \__, |\__\___|_| \_\__,_|___/ \__\___|_|  |___/   ║
    ║        |___/                                             ║
    ║                Speed Test Server v1.0                    ║
    ╚══════════════════════════════════════════════════════════╝
    {Style.RESET_ALL}"""
    print(banner)
colorama.init()

class SpeedTestClient:
    TEAM_NAME = "ByteBusters"
    OFFER_MSG_TYPE = 0x2
    MAGIC_COOKIE = 0xabcddcba
    REQUEST_MSG_TYPE = 0x3

    def __init__(self):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) ## delete before run between 2 computer
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)
        self.udp_socket.bind(('', 13117))
        
        self.running = True
        signal.signal(signal.SIGINT, self.stop)

    def stop(self, signum, frame):
        print(f"{Fore.RED}Shutting down the client gracefully...{Style.RESET_ALL}")
        self.running = False

    def get_user_parameters(self) -> Tuple[int, int, int]:
        """Get file size, TCP and UDP connections from the user."""
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
        """Wait for server offers and return server details."""
        print(f"{Fore.CYAN}Client started, listening for offer requests...{Style.RESET_ALL}")
        while self.running:
            try:
                data, addr = self.udp_socket.recvfrom(1024)
                magic_cookie, msg_type, udp_port, tcp_port = struct.unpack('!IbHH', data)

                if magic_cookie == self.MAGIC_COOKIE and msg_type == self.OFFER_MSG_TYPE:
                    print(f"{Fore.GREEN}Received offer from {addr[0]} (UDP: {udp_port}, TCP: {tcp_port}){Style.RESET_ALL}")
                    return addr[0], udp_port, tcp_port
            except Exception as e:
                print(f"{Fore.RED}Error receiving offer: {str(e)}{Style.RESET_ALL}")

    def handle_tcp_transfer(self, server_ip: str, server_port: int, file_size: int, transfer_num: int) -> None:
        """Handle TCP transfer and log progress."""
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

            print(f"{Fore.GREEN}TCP transfer #{transfer_num} finished: Time {total_time:.2f}s, Speed {speed:.2f} bps{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}TCP transfer error: {str(e)}{Style.RESET_ALL}")
        finally:
            sock.close()

    def handle_udp_transfer(self, server_ip: str, server_port: int, file_size: int, transfer_num: int) -> None:
        """Handle UDP transfer and calculate statistics."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1.0)

            request = struct.pack('!IbQ', self.MAGIC_COOKIE, self.REQUEST_MSG_TYPE, file_size)
            sock.sendto(request, (server_ip, server_port))

            start_time = time.time()
            received_segments = set()
            total_segments = (file_size + 1024 - 1) // 1024

            while True:
                try:
                    data, _ = sock.recvfrom(2048)

                    # Check packet size before unpacking
                    if len(data) < 21:
                        print(f"{Fore.RED}Received packet too short: {len(data)} bytes{Style.RESET_ALL}")
                        continue

                    magic_cookie, msg_type, total_segs, current_seg = struct.unpack('!IbQQ', data[:21])

                    if magic_cookie != self.MAGIC_COOKIE or msg_type != 0x4:
                        continue

                    received_segments.add(current_seg)

                    if len(received_segments) >= total_segs:
                        break

                except socket.timeout:
                    break

            total_time = time.time() - start_time
            success_rate = (len(received_segments) / total_segments) * 100
            speed = (len(received_segments) * 1024 * 8) / total_time

            print(f"{Fore.GREEN}UDP transfer #{transfer_num} finished: Time {total_time:.2f}s, Speed {speed:.2f} bps, Success Rate {success_rate:.2f}%{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}UDP transfer error: {str(e)}{Style.RESET_ALL}")
        finally:
            sock.close()

    def run_speed_test(self):
        """Run the speed test by managing threads for TCP and UDP transfers."""
        print_banner()
        file_size, tcp_count, udp_count = self.get_user_parameters()

        while self.running:
            server_ip, udp_port, tcp_port = self.wait_for_server()

            threads: List[threading.Thread] = []

            for i in range(tcp_count):
                thread = threading.Thread(target=self.handle_tcp_transfer, args=(server_ip, tcp_port, file_size, i + 1))
                threads.append(thread)

            for i in range(udp_count):
                thread = threading.Thread(target=self.handle_udp_transfer, args=(server_ip, udp_port, file_size, i + 1))
                threads.append(thread)

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join()

            

            print(f"{Fore.CYAN}All transfers completed. Listening for new offers...{Style.RESET_ALL}")


if __name__ == "__main__":
    client = SpeedTestClient()
    client.run_speed_test()
