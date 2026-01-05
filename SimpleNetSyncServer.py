# Config

DEFAULT_PORT = 55555




# Implementation

import sys
import socket
import signal
import json
from typing import Any


_guid = -1
def new_GUID() -> int:
        global _guid
        _guid += 1
        return _guid


port = DEFAULT_PORT
if len(sys.argv) >= 2:
        port = int(sys.argv[1])

clients: list[(str, int)] = []
client_ids: dict[(str, int), int] = {}
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
        if addr not in clients:
                clients.append(addr)
                client_ids[addr] = new_GUID()
                client_packet_seq_numbers[client_ids[addr]] = -1
                packet_seq_number += 1
                s.sendto(client_ids[addr].to_bytes(8, "little"), addr)
                print(f"Client {client_ids[addr]} connected")
                continue
        data_packet_seq = int.from_bytes(data[:8], "little")
        if data_packet_seq <= client_packet_seq_numbers[client_ids[addr]]:
                continue
        client_packet_seq_numbers[client_ids[addr]] = data_packet_seq
        client_states[client_ids[addr]] = data[8:].decode("ascii")
        packet_seq_number += 1
        for client in clients:
                s.sendto(
                        (
                                packet_seq_number.to_bytes(8, "little") +
                                json.dumps(client_states, separators=(',', ':')).encode("ascii")
                        ),
                        client
                )