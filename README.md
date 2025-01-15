# Speed Test Client-Server Application

## Introduction
This project is a client-server application developed for the Intro to Computer Networks 2024 Hackathon. The application allows users to test network speed by comparing UDP and TCP data transfers. It implements the required functionality to send and receive data over the network, providing detailed performance metrics.

## Features
- **Multithreaded Server and Client**: Supports simultaneous connections for both UDP and TCP transfers.
- **Packet-Based Communication**: Implements structured packets for offers, requests, and payloads.
- **Statistics Collection**: Measures total transfer time, speed, and packet success rate.
- **Dynamic Configuration**: Allows users to specify file sizes and number of connections.
- **Error Handling**: Includes graceful handling of timeouts, invalid packets, and other network issues.

## Architecture
### Server
- **UDP Offer Broadcast**: Continuously broadcasts availability to clients.
- **TCP Handling**: Processes file transfer requests over TCP.
- **UDP Payload Handling**: Responds to UDP file transfer requests with segmented packets.

### Client
- **Server Discovery**: Uses UDP to discover available servers.
- **Transfer Modes**: Supports both TCP and UDP transfers.
- **Performance Metrics**: Calculates and logs transfer speeds and packet loss rates.

## Packet Formats
### Offer Packet
| Field            | Size   | Description                         |
|------------------|--------|-------------------------------------|
| Magic Cookie     | 4 bytes | Fixed identifier (0xabcddcba)       |
| Message Type     | 1 byte  | Offer message type (0x2)            |
| Server UDP Port  | 2 bytes | UDP port for the server             |
| Server TCP Port  | 2 bytes | TCP port for the server             |

### Request Packet
| Field         | Size   | Description                      |
|---------------|--------|----------------------------------|
| Magic Cookie  | 4 bytes | Fixed identifier (0xabcddcba)    |
| Message Type  | 1 byte  | Request message type (0x3)       |
| File Size     | 8 bytes | Requested file size in bytes     |

### Payload Packet
| Field               | Size   | Description                          |
|---------------------|--------|--------------------------------------|
| Magic Cookie        | 4 bytes | Fixed identifier (0xabcddcba)        |
| Message Type        | 1 byte  | Payload message type (0x4)           |
| Total Segment Count | 8 bytes | Total number of segments in the file |
| Current Segment     | 8 bytes | Index of the current segment         |
| Payload             | Variable | Data for the segment                |

## Requirements
- Python 3.x
- Dependencies:
  - `scapy>=2.5.0`
- colorama package (`pip install colorama`)

## Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # For Windows: .\venv\Scripts\activate
   ```

## Usage
### Starting the Server
1. Navigate to the project directory.
2. Run the server:
   ```
   python server.py
   ```

### Starting the Client
1. Navigate to the project directory.
2. Run the client:
   ```
   python client.py
   ```
3. Follow the on-screen prompts to specify file size and connection parameters.

## Example Run
### Server Output
```
[SUCCESS] Server started, listening on IP address 192.168.1.10
[INFO] TCP port: 5000, UDP port: 5001
[INFO] New TCP connection from 192.168.1.20
[SUCCESS] TCP transfer to 192.168.1.20 completed
```

### Client Output
```
[INFO] Welcome to the Speed Test Client!
[INFO] Client started, listening for offer requests...
[SUCCESS] Received offer from 192.168.1.10
[SUCCESS] TCP transfer #1 finished, total time: 3.55 seconds, total speed: 5.4 bits/second
[SUCCESS] UDP transfer #1 finished, total time: 3.55 seconds, total speed: 5.4 bits/second, percentage of packets received successfully:100%
```

## Testing
- Test on a stable network environment (e.g., a personal hotspot) for optimal results.
- Use various file sizes and connection counts to evaluate performance.

---
Good luck and have fun!


