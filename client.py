import socket
import struct
import threading
import time
from typing import List, Tuple
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

class SpeedTestClient:
    MAGIC_COOKIE = 0xabcddcba
    OFFER_MSG_TYPE = 0x2
    REQUEST_MSG_TYPE = 0x3

    def __init__(self):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.bind(('', 13117))

    def get_user_parameters(self):
        file_size = int(input("Enter file size (bytes): "))
        tcp_connections = int(input("Enter number of TCP connections: "))
        udp_connections = int(input("Enter number of UDP connections: "))
        return file_size, tcp_connections, udp_connections

    def wait_for_server(self):
        while True:
            data, addr = self.udp_socket.recvfrom(1024)
            magic_cookie, msg_type, udp_port, tcp_port = struct.unpack('!IbHH', data)
            if magic_cookie == self.MAGIC_COOKIE and msg_type == self.OFFER_MSG_TYPE:
                print(f"Received offer from {addr[0]}.")
                return addr[0], udp_port, tcp_port

    def handle_tcp_transfer(self, server_ip, server_port, file_size):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((server_ip, server_port))
            sock.sendall(f"{file_size}\n".encode())
            start_time = time.time()
            received = 0
            while received < file_size:
                chunk = sock.recv(8192)
                if not chunk:
                    break
                received += len(chunk)
            total_time = time.time() - start_time
            speed = (received * 8) / total_time
            print(f"TCP transfer finished: {total_time:.2f} sec, {speed:.2f} bps.")

    def handle_udp_transfer(self, server_ip, server_port, file_size):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            request = struct.pack('!IbQ', self.MAGIC_COOKIE, self.REQUEST_MSG_TYPE, file_size)
            sock.sendto(request, (server_ip, server_port))
            start_time = time.time()
            received_bytes = 0
            while True:
                try:
                    data, _ = sock.recvfrom(2048)
                    received_bytes += len(data) - struct.calcsize('!IbQQ')
                except socket.timeout:
                    break
            total_time = time.time() - start_time
            speed = (received_bytes * 8) / total_time
            print(f"UDP transfer finished: {total_time:.2f} sec, {speed:.2f} bps.")

    def run_speed_test(self):
        file_size, tcp_count, udp_count = self.get_user_parameters()
        while True:
            print("Listening for server offers...")
            server_ip, udp_port, tcp_port = self.wait_for_server()

            threads = []
            for _ in range(tcp_count):
                t = threading.Thread(target=self.handle_tcp_transfer, args=(server_ip, tcp_port, file_size))
                threads.append(t)

            for _ in range(udp_count):
                t = threading.Thread(target=self.handle_udp_transfer, args=(server_ip, udp_port, file_size))
                threads.append(t)

            for t in threads:
                t.start()
            for t in threads:
                t.join()

if __name__ == "__main__":
    client = SpeedTestClient()
    client.run_speed_test()
