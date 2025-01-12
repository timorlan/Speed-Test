"""
Configuration settings for the Speed Test application.
Contains all configurable parameters to avoid hard-coding values in the code.
"""
import logging
from typing import Dict, Any

# Network Configuration
NETWORK_CONFIG: Dict[str, Any] = {
    'BROADCAST_PORT': 13117,
    'MAGIC_COOKIE': 0xabcddcba,
    'OFFER_MSG_TYPE': 0x2,
    'REQUEST_MSG_TYPE': 0x3,
    'PAYLOAD_MSG_TYPE': 0x4,
    'BUFFER_SIZE': 8192,
    'SEGMENT_SIZE': 1024,
    'MAX_PACKET_SIZE': 2048,
}

# Timing Configuration
TIMING_CONFIG: Dict[str, float] = {
    'BROADCAST_INTERVAL': 1.0,  # seconds between broadcast messages
    'CONNECTION_TIMEOUT': 5.0,  # seconds to wait for connection
    'TRANSFER_TIMEOUT': 10.0,   # seconds to wait for transfer completion
    'UDP_PACKET_TIMEOUT': 0.05, # seconds to wait for UDP packets
    'RECONNECT_DELAY': 1.0,    # seconds between reconnection attempts
}

# Performance Configuration
PERFORMANCE_CONFIG: Dict[str, Any] = {
    'TCP_BUFFER_SIZE': 8192,
    'UDP_BUFFER_SIZE': 4 * 1024 * 1024,  # 4MB buffer
    'MAX_RECONNECT_ATTEMPTS': 3,
    'UDP_BURST_SIZE': 32,
    'SIMULATED_PACKET_LOSS': 0.05,  # 5% packet loss simulation
}

# Logging Configuration
LOGGING_CONFIG: Dict[str, Any] = {
    'version': 1,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'detailed',
            'level': logging.INFO
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'speedtest.log',
            'formatter': 'detailed',
            'level': logging.DEBUG
        }
    },
    'loggers': {
        'speedtest': {
            'handlers': ['console', 'file'],
            'level': logging.DEBUG,
            'propagate': False
        }
    }
}

# Error Messages
ERROR_MESSAGES = {
    'INVALID_INPUT': 'Invalid input: Values must be positive numbers',
    'CONNECTION_FAILED': 'Failed to connect to server: {}',
    'TRANSFER_FAILED': 'Transfer failed: {}',
    'INVALID_PACKET': 'Received invalid packet: {}',
    'TIMEOUT': 'Operation timed out: {}',
}

TEAM_NAME = "ByteBusters"