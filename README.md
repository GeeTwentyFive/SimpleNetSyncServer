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


# Custom client example
TODO