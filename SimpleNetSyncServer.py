# Config

DEFAULT_PORT = 55555
TIMEOUT = 10.0




# Implementation

import sys
import socket
import signal
import time
import json
from typing import Any


CONNECT_REQUEST_PACKET = -1


_guid = -1
def new_GUID() -> int:
        global _guid
        _guid += 1
        return _guid


port = DEFAULT_PORT
if len(sys.argv) >= 2:
        port = int(sys.argv[1])

unverified_clients: list[(str, int)] = []
clients: list[(str, int)] = []
client_ids: dict[(str, int), int] = {}
client_last_packet_times: dict[int, float] = {}
client_packet_seq_numbers: dict[int, int] = {}
client_states: dict[int, Any] = {}

packet_seq_number = 0

s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
s.bind(("::", port))
keep_running = True
signal.signal(signal.SIGINT, lambda: (keep_running := False))
print(f"Server started on port {port}")
while keep_running:
        data, addr = s.recvfrom(65536)

        # Handle non-existing-client packets
        if addr not in clients:
                if addr not in unverified_clients:
                        if int.from_bytes(data[:8], "little") != CONNECT_REQUEST_PACKET: continue
                        # New connection attempt
                        unverified_clients.append(addr)
                        client_ids[addr] = new_GUID()
                        s.sendto(client_ids[addr].to_bytes(8, "little"), addr)
                else:
                        if int.from_bytes(data[:8], "little") == CONNECT_REQUEST_PACKET: continue
                        # Connection verified, add as client
                        unverified_clients.remove(addr)
                        clients.append(addr)
                        client_last_packet_times[client_ids[addr]] = time.monotonic()
                        print(f"Client {client_ids[addr]} connected")
                        # (save received client state)
                        client_packet_seq_numbers[client_ids[addr]] = int.from_bytes(data[:8], "little")
                        client_states[client_ids[addr]] = data[8:].decode("ascii")
                continue

        # Handle timeouts
        for client in clients:
                if (
                        time.monotonic() -
                        client_last_packet_times[client_ids[client]]
                ) > TIMEOUT:
                        clients.remove(client)
                        print(f"Client {client_ids[client]} disconnected")
        
        client_last_packet_times[client_ids[addr]] = time.monotonic()

        # Save received client state
        data_packet_seq = int.from_bytes(data[:8], "little")
        if data_packet_seq <= client_packet_seq_numbers[client_ids[addr]]:
                continue
        client_packet_seq_numbers[client_ids[addr]] = data_packet_seq
        client_states[client_ids[addr]] = data[8:].decode("ascii")

        # Sync client states
        packet_seq_number += 1
        for client in clients:
                s.sendto(
                        (
                                packet_seq_number.to_bytes(8, "little") +
                                json.dumps(client_states, separators=(',', ':')).encode("ascii")
                        ),
                        client
                )