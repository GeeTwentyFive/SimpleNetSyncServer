# Config

DEFAULT_PORT = 55555
TIMEOUT = 10.0




# Implementation

import sys
import miniupnpc
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

print(f"Attempting to forward UDP {port} via UPnP...")
try:
        upnp = miniupnpc.UPnP()
        try: upnp.discover()
        except: pass
        upnp.selectigd()
        upnp.addportmapping(
                port,
                "UDP",
                upnp.lanaddr,
                port,
                "UPnP mapping",
                ""
        )
except Exception as e:
        print("UPnP ERROR: " + str(e))

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
                        if int.from_bytes(data[:8], "little", signed=True) != CONNECT_REQUEST_PACKET: continue
                        # New connection attempt
                        unverified_clients.append(addr)
                        client_ids[addr] = new_GUID()
                        s.sendto(
                                (
                                        (-1).to_bytes(8, "little", signed=True) +
                                        client_ids[addr].to_bytes(8, "little", signed=True)
                                ),
                                addr
                        )
                else:
                        if int.from_bytes(data[:8], "little", signed=True) < 0: continue
                        # Connection verified, add as client
                        unverified_clients.remove(addr)
                        clients.append(addr)
                        client_last_packet_times[client_ids[addr]] = time.monotonic()
                        print(f"Client {client_ids[addr]} connected")
                        # (save received client state)
                        client_packet_seq_numbers[client_ids[addr]] = int.from_bytes(data[:8], "little", signed=True)
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
        data_packet_seq = int.from_bytes(data[:8], "little", signed=True)
        if data_packet_seq <= client_packet_seq_numbers[client_ids[addr]]:
                continue
        client_packet_seq_numbers[client_ids[addr]] = data_packet_seq
        client_states[client_ids[addr]] = data[8:].decode("ascii")

        client_states_json = json.dumps(client_states, separators=(',', ':')).encode("ascii")
        if len(client_states_json) > 65535-8:
                print("WARNING: client_states_json size exceeds UDP packet max")

        # Sync client states
        packet_seq_number += 1
        for client in clients:
                s.sendto(
                        (
                                packet_seq_number.to_bytes(8, "little", signed=True) +
                                client_states_json
                        ),
                        client
                )