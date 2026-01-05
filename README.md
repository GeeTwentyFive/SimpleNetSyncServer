General-purpose cross-platform networked state synchronization server

Python client library: https://github.com/GeeTwentyFive/PySimpleNetSync

GDScript client library: https://github.com/GeeTwentyFive/GodotSimpleNetSync


# Usage
`SimpleNetSyncServer [PORT]`


# Protocol

Client keeps sending packet `-1` (i64) until server replies with `-1` (i64) + `id`

After receiving `-1` (i64), server sends:
```
i64 -1, i64 client_id
```
(`client_id` is ID of that client. Used as a key in states dict)

(Then, the server must receive at least one regular communication packet from the client for the client to be considered "connected" and start receiving the states of all clients)

For all subsequent communication (both send and receive):
```
i64 packet_num, str payload
```
(From server to client: `payload` is an `{int: str}` dictionary of client states where the keys are `client_id`'s)

(From client: `payload` is placed inside client states dict on server at key `client_id` (already associated with client (based on address) on server))

(`packet_num` is just a number which is incremented for each new packet)


# Minimal custom client example
```py
import socket
import json
import threading
from time import sleep


s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)

client_states = {}


def receive_handler():
        global s
        global client_states
        server_packet_seq_num = -1
        while True:
                data, _ = s.recvfrom(65536)
                if int.from_bytes(data[:8], "little", signed=True) <= server_packet_seq_num: continue
                server_packet_seq_num = int.from_bytes(data[:8], "little", signed=True)
                client_states = json.loads(data[8:].decode("ascii"))

local_client_state = 0
local_packet_seq_num = -1
local_client_id = -1

# Keep sending ID request until you receive your ID
while True:
        s.sendto((-1).to_bytes(8, "little", signed=True), ("::1", 55555))
        data, _ = s.recvfrom(65536)
        if int.from_bytes(data[:8], "little", signed=True) == -1:
                local_client_id = int.from_bytes(data[8:], "little", signed=True)
                break
        sleep(0.5)

threading.Thread(target=receive_handler).start()

# Sync local state & print received state
while True:
        print(client_states)
        local_client_state += 1
        local_packet_seq_num += 1
        s.sendto(
                (
                        local_packet_seq_num.to_bytes(8, "little", signed=True) +
                        str(local_client_state).encode("ascii")
                ),
                ("::1", 55555)
        )
        sleep(0.1)
```