General-purpose cross-platform networked state synchronization server

Python client library: https://github.com/GeeTwentyFive/PySimpleNetSync


# Usage
`SimpleNetSyncServer [PORT]`


# Protocol

After first packet received, server sends:
```
i64 client_id
```

For all subsequent communication (both send and receive):
```
i64 packet_num, str payload
```
(`payload` is an `{int: str}` dictionary where the keys are `client_id`'s)

(`packet_num` is just a number which is incremented for each new packet)


# Custom client example
```py
import socket
import json
import threading
from time import sleep


client_states = {}

s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)

def receive_handler():
        global s
        global client_states
        server_packet_seq_num = -1
        while True:
                data, _ = s.recvfrom(65536)
                if int.from_bytes(data[:8]) <= server_packet_seq_num: continue
                server_packet_seq_num = int.from_bytes(data[:8])
                client_states = json.loads(data[8:].decode("ascii"))

local_client_state = 0
local_packet_seq_num = -1
local_client_id = -1

s.sendto(bytes(1), ("::1", 55555))
data, _ = s.recvfrom(65536)
local_client_id = int.from_bytes(data)

threading.Thread(target=receive_handler).start()

while True:
        print(client_states)
        local_client_state += 1
        local_packet_seq_num += 1
        s.sendto(
                (
                        local_packet_seq_num.to_bytes(8) +
                        str(local_client_state).encode("ascii")
                ),
                ("::1", 55555)
        )
        sleep(0.1)
```