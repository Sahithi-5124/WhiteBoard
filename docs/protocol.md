# WhiteBoard – Client-Server Communication Protocol

**Project:** LAN-Based Multi-User Collaborative Whiteboard  
**Protocol Version:** 1.0  
**Transport:** TCP  
**Message Format:** JSON  
**Encoding:** UTF-8  
**Message Framing:** 4-byte unsigned big-endian length prefix  

---

## 1. Overview

This document describes the communication protocol used between the WhiteBoard server and its connected clients.

The application allows multiple users connected to the same Local Area Network (LAN) to work on a shared whiteboard in real time.

The protocol defines:

- Client-server communication.
- Message structure and message types.
- Message framing and serialization.
- Room and participant communication.
- Whiteboard operation synchronization.
- Server-side validation and authorization.
- Error handling.
- Message ordering and duplicate request handling.
- Reconnection and state synchronization.

All clients must follow the same protocol when exchanging data with the server.

## 2. Communication Architecture

The application follows a centralized client-server architecture.

- The server manages client connections, rooms, participants and shared board state.
- Clients send requests to the server for operations such as creating or modifying objects.
- The server validates incoming requests before processing them.
- Accepted operations are applied to the server's shared state.
- The server broadcasts accepted changes to the relevant clients.
- Clients update their local interfaces based on the received server messages.

The server acts as the authoritative source of shared room state.

### Communication Flow

1. A client establishes a TCP connection with the server.
2. The client sends a `CONNECT` request.
3. The server validates the request and responds with `CONNECT_SUCCESS` or `CONNECT_ERROR`.
4. The client creates or joins a room.
5. The client sends operations such as drawing, object editing or chat messages.
6. The server validates and processes the requests.
7. The server acknowledges accepted operations and broadcasts the resulting events to other relevant clients.

## 3. Network Configuration

The server listens for incoming connections on a configurable host and port.

| Parameter | Description |
|---|---|
| Host | Server network interface |
| Default bind address | `0.0.0.0` |
| Port | Configurable TCP port |
| Transport | TCP |
| Encoding | UTF-8 |

The server uses `0.0.0.0` as its default bind address so that clients can connect through the available network interfaces.

Clients connect using the server computer's LAN IP address and the configured port number.

The port number will be finalized during implementation.

## 4. Message Framing

TCP is a byte-stream protocol and does not preserve individual message boundaries. A message sent using one `send()` call may be received through multiple `recv()` calls.

To identify individual messages, the application uses length-prefixed framing.

### 4.1 Frame Structure

Each message consists of two parts:

| Component | Size | Description |
|---|---:|---|
| Length prefix | 4 bytes | Size of the message body |
| Message body | Variable | UTF-8 encoded JSON |

The length prefix is an unsigned 32-bit integer in network byte order (big-endian).

### 4.2 Frame Representation

```text
[4-byte message length][UTF-8 JSON message]
```

### 4.3 Sending Procedure

1. Convert the message dictionary into a JSON string.
2. Encode the JSON string using UTF-8.
3. Calculate the length of the encoded message.
4. Convert the length into a 4-byte big-endian integer.
5. Send the length prefix followed by the message body.

### 4.4 Receiving Procedure

1. Read exactly 4 bytes from the socket.
2. Decode the bytes as an unsigned big-endian integer.
3. Check whether the message length is within the configured limit.
4. Read exactly the specified number of bytes.
5. Decode the message body using UTF-8.
6. Parse the JSON data.
7. Validate the message structure before processing it.

The receiving implementation must handle partial TCP reads. A single `recv()` call is not guaranteed to return all the requested bytes.

If the connection closes before the complete frame is received, the incomplete message must be discarded.

### 4.5 Message Size Limit

The initial maximum JSON message size is **1 MiB (1,048,576 bytes)**.

This limit should be configurable.

Large binary files and images will use a separate transfer mechanism instead of being embedded directly into ordinary JSON messages.

## 5. Standard Message Structure

All application-level messages follow a common envelope structure. This provides a consistent format for communication between the server and clients.

### 5.1 Standard Envelope

```json
{
    "protocol_version": 1,
    "type": "MESSAGE_TYPE",
    "message_id": "msg_001",
    "room_id": "room_101",
    "sender_id": "user_01",
    "timestamp": 1793990000,
    "payload": {}
}
```

### 5.2 Field Descriptions

| Field | Type | Description |
|---|---|---|
| `protocol_version` | Integer | Protocol version |
| `type` | String | Message type |
| `message_id` | String | Unique identifier for the message |
| `room_id` | String / null | Associated room, if applicable |
| `sender_id` | String / null | Sender identity |
| `timestamp` | Number | Unix timestamp |
| `payload` | Object | Message-specific data |

### 5.3 General Rules

- `protocol_version` must be supported by the receiving application.
- `type` must contain a recognized message type.
- `message_id` must be unique for each client request.
- `room_id` must refer to a valid room when the operation requires one.
- `sender_id` is informational and must not be treated as proof of identity.
- The server determines the actual sender using the connection context.
- The server generates authoritative timestamps for accepted events.
- `payload` must be a JSON object.

For messages that are not associated with a room, `room_id` may be `null`.

For server-originated messages, `sender_id` may be `null` or a designated server identifier.

## 6. Message Categories

Messages exchanged between the server and clients can be grouped into three categories.

### 6.1 Client Requests

These messages are initiated by clients and sent to the server.

Examples include:

- `CONNECT`
- `CREATE_ROOM`
- `JOIN_ROOM`
- `CREATE_OBJECT`
- `UPDATE_OBJECT`
- `DELETE_OBJECT`
- `CHAT_MESSAGE`
- `UNDO_REQUEST`
- `REDO_REQUEST`

### 6.2 Server Responses

These messages communicate the result of a client request.

Examples include:

- `CONNECT_SUCCESS`
- `CONNECT_ERROR`
- `ROOM_CREATED`
- `ROOM_JOINED`
- `OPERATION_ACCEPTED`
- `ROOM_ERROR`
- `ERROR`
- `BOARD_SNAPSHOT`

### 6.3 Server Events

These messages notify clients about changes in the shared application state.

Examples include:

- `USER_JOINED`
- `USER_LEFT`
- `OBJECT_CREATED`
- `OBJECT_UPDATED`
- `OBJECT_DELETED`
- `CHAT_BROADCAST`
- `CURSOR_UPDATE`

A client request must not be treated as an accepted event until the server has validated and processed it.

## 7. Message Types

The following message types are used for communication between the server and clients.

### 7.1 Connection Management

| Message Type | Direction | Purpose |
|---|---|---|
| `CONNECT` | Client → Server | Request connection registration |
| `CONNECT_SUCCESS` | Server → Client | Connection accepted |
| `CONNECT_ERROR` | Server → Client | Connection rejected |
| `DISCONNECT` | Client → Server | Gracefully disconnect |
| `USER_JOINED` | Server → Clients | Notify room participants |
| `USER_LEFT` | Server → Clients | Notify room participants |
| `RECONNECT` | Client → Server | Request session recovery |

### 7.2 Room Management

| Message Type | Direction | Purpose |
|---|---|---|
| `CREATE_ROOM` | Client → Server | Create a room |
| `JOIN_ROOM` | Client → Server | Join an existing room |
| `LEAVE_ROOM` | Client → Server | Leave the current room |
| `ROOM_CREATED` | Server → Client | Confirm room creation |
| `ROOM_JOINED` | Server → Client | Confirm room entry |
| `ROOM_ERROR` | Server → Client | Report a room-related error |

### 7.3 Whiteboard Operations

| Message Type | Direction | Purpose |
|---|---|---|
| `CREATE_OBJECT` | Client → Server | Create a board object |
| `UPDATE_OBJECT` | Client → Server | Modify a board object |
| `DELETE_OBJECT` | Client → Server | Delete a board object |
| `OBJECT_CREATED` | Server → Clients | Broadcast object creation |
| `OBJECT_UPDATED` | Server → Clients | Broadcast object modification |
| `OBJECT_DELETED` | Server → Clients | Broadcast object deletion |
| `BOARD_SNAPSHOT` | Server → Client | Send complete board state |

### 7.4 Collaboration

| Message Type | Direction | Purpose |
|---|---|---|
| `CURSOR_UPDATE` | Client ↔ Server | Synchronize cursor positions |
| `CHAT_MESSAGE` | Client → Server | Send a chat message |
| `CHAT_BROADCAST` | Server → Clients | Distribute a chat message |
| `UNDO_REQUEST` | Client → Server | Request undo |
| `REDO_REQUEST` | Client → Server | Request redo |

### 7.5 General Responses

| Message Type | Direction | Purpose |
|---|---|---|
| `OPERATION_ACCEPTED` | Server → Client | Confirm an accepted operation |
| `ERROR` | Server → Client | Report a general error |

Additional message types can be introduced when required. New types and their payload structures should be documented before they are used by the clients and server.

## 8. Connection Protocol

### 8.1 CONNECT

A client sends a `CONNECT` message to register with the server.

```json
{
    "protocol_version": 1,
    "type": "CONNECT",
    "message_id": "msg_001",
    "room_id": null,
    "sender_id": null,
    "timestamp": 1793990000,
    "payload": {
        "username": "Sahithi"
    }
}
```

The server validates the request and registers the client if the request is accepted.

### 8.2 CONNECT_SUCCESS

If the connection request is accepted, the server responds with `CONNECT_SUCCESS`.

```json
{
    "protocol_version": 1,
    "type": "CONNECT_SUCCESS",
    "message_id": "msg_002",
    "room_id": null,
    "sender_id": null,
    "timestamp": 1793990001,
    "payload": {
        "user_id": "user_01",
        "username": "Sahithi",
        "server_version": "1.0"
    }
}
```

The server assigns a unique user ID to the connected client.

### 8.3 CONNECT_ERROR

If the connection request is rejected, the server sends `CONNECT_ERROR`.

```json
{
    "protocol_version": 1,
    "type": "CONNECT_ERROR",
    "message_id": "msg_003",
    "room_id": null,
    "sender_id": null,
    "timestamp": 1793990001,
    "payload": {
        "error_code": "INVALID_USERNAME",
        "message": "Username is invalid."
    }
}
```

## 9. Room Management Protocol

Rooms allow users to collaborate on separate whiteboards. Each room maintains its own participants and shared board state.

### 9.1 CREATE_ROOM

A connected client sends `CREATE_ROOM` to request the creation of a new room.

```json
{
    "protocol_version": 1,
    "type": "CREATE_ROOM",
    "message_id": "msg_010",
    "room_id": null,
    "sender_id": "user_01",
    "timestamp": 1793990002,
    "payload": {
        "room_name": "Design Discussion"
    }
}
```

The server creates the room and assigns it a unique room ID.

### 9.2 ROOM_CREATED

After successful room creation, the server responds with `ROOM_CREATED`.

```json
{
    "protocol_version": 1,
    "type": "ROOM_CREATED",
    "message_id": "msg_011",
    "room_id": "room_101",
    "sender_id": null,
    "timestamp": 1793990003,
    "payload": {
        "room_name": "Design Discussion",
        "host_id": "user_01"
    }
}
```

### 9.3 JOIN_ROOM

A client sends `JOIN_ROOM` to enter an existing room.

```json
{
    "protocol_version": 1,
    "type": "JOIN_ROOM",
    "message_id": "msg_012",
    "room_id": "room_101",
    "sender_id": "user_02",
    "timestamp": 1793990004,
    "payload": {}
}
```

### 9.4 ROOM_JOINED

If the request is successful, the server sends `ROOM_JOINED` with the room details and current participant list.

```json
{
    "protocol_version": 1,
    "type": "ROOM_JOINED",
    "message_id": "msg_013",
    "room_id": "room_101",
    "sender_id": null,
    "timestamp": 1793990005,
    "payload": {
        "room_name": "Design Discussion",
        "participants": [
            {
                "user_id": "user_01",
                "username": "Sahithi"
            },
            {
                "user_id": "user_02",
                "username": "Alex"
            }
        ]
    }
}
```

Room-specific operations are accepted only from connected users who are members of the respective room.

`LEAVE_ROOM` is used when a client wants to leave its current room. The server updates the participant list and notifies the remaining members using the appropriate participant event.

## 10. Whiteboard Object Protocol

All whiteboard objects use a common representation so that different object types can be handled consistently by the server.

### 10.1 Common Object Structure

```json
{
    "object_id": "obj_001",
    "object_type": "rectangle",
    "owner_id": "user_01",
    "position": {
        "x": 100,
        "y": 150
    },
    "dimensions": {
        "width": 200,
        "height": 100
    },
    "rotation": 0,
    "style": {
        "stroke_color": "#000000",
        "fill_color": "#FFFFFF",
        "stroke_width": 2
    },
    "locked": false
}
```

### Object Fields

| Field | Description |
|---|---|
| `object_id` | Unique object identifier |
| `object_type` | Type of object |
| `owner_id` | ID of the user who created the object |
| `position` | Object coordinates |
| `dimensions` | Object width and height |
| `rotation` | Rotation angle in degrees |
| `style` | Visual properties |
| `locked` | Indicates whether the object is locked |

Additional properties can be included depending on the object type.

Supported object types include:

- Freehand paths
- Lines and arrows
- Rectangles and ellipses
- Text objects
- Images
- Stickers
- Sticky notes

Each object type will have its own additional properties where required.

### 10.2 CREATE_OBJECT

A client sends `CREATE_OBJECT` when a new object is added to the board.

```json
{
    "protocol_version": 1,
    "type": "CREATE_OBJECT",
    "message_id": "msg_020",
    "room_id": "room_101",
    "sender_id": "user_01",
    "timestamp": 1793990010,
    "payload": {
        "object": {
            "object_id": "obj_001",
            "object_type": "rectangle",
            "owner_id": "user_01",
            "position": {
                "x": 100,
                "y": 150
            },
            "dimensions": {
                "width": 200,
                "height": 100
            },
            "rotation": 0,
            "style": {
                "stroke_color": "#000000",
                "fill_color": "#FFFFFF",
                "stroke_width": 2
            },
            "locked": false
        }
    }
}
```

The server validates the object data and adds the object to the room's shared board state.

### 10.3 UPDATE_OBJECT

A client sends `UPDATE_OBJECT` when an existing object is modified.

```json
{
    "protocol_version": 1,
    "type": "UPDATE_OBJECT",
    "message_id": "msg_021",
    "room_id": "room_101",
    "sender_id": "user_01",
    "timestamp": 1793990011,
    "payload": {
        "object_id": "obj_001",
        "changes": {
            "position": {
                "x": 150,
                "y": 200
            },
            "rotation": 30
        }
    }
}
```

The server checks whether the object exists and validates the requested changes before updating the shared object state.

### 10.4 DELETE_OBJECT

A client sends `DELETE_OBJECT` to remove an object from the board.

```json
{
    "protocol_version": 1,
    "type": "DELETE_OBJECT",
    "message_id": "msg_022",
    "room_id": "room_101",
    "sender_id": "user_01",
    "timestamp": 1793990012,
    "payload": {
        "object_id": "obj_001"
    }
}
```

The server verifies that the object exists and that the requesting user has permission to delete it.

### 10.5 Server Object Events

After successfully processing an object operation, the server broadcasts the corresponding event to the relevant room participants.

- `OBJECT_CREATED`
- `OBJECT_UPDATED`
- `OBJECT_DELETED`

These events contain the authoritative object data or the accepted changes.

## 11. Acknowledgements and Operation Ordering

Client requests and their resulting server events are treated as separate messages.

### 11.1 OPERATION_ACCEPTED

When an operation is successfully processed, the server sends `OPERATION_ACCEPTED` to the requesting client.

```json
{
    "protocol_version": 1,
    "type": "OPERATION_ACCEPTED",
    "message_id": "ack_001",
    "room_id": "room_101",
    "sender_id": null,
    "timestamp": 1793990013,
    "payload": {
        "request_id": "msg_020",
        "operation_id": "op_001",
        "sequence_number": 15
    }
}
```

The `request_id` identifies the original client request, while `operation_id` identifies the accepted operation.

### 11.2 Sequence Numbers

Every accepted state-changing room operation receives a server-generated sequence number.

The following rules apply:

1. Sequence numbers start from an agreed initial value for each room.
2. Sequence numbers increase monotonically within a room.
3. The server assigns sequence numbers after validating operations.
4. Clients use sequence numbers to determine the correct event order.
5. Rejected operations do not consume sequence numbers.
6. Clients must not generate sequence numbers independently.

Sequence numbers help ensure that all participants apply shared operations in the same order.

### 11.3 Operation IDs

Every accepted state-changing operation receives a unique server-generated `operation_id`.

This identifier can be used for operation tracking, history management and undo/redo functionality.

## 12. Duplicate Request Handling

Each client request must contain a unique `message_id`.

The server maintains a record of processed request IDs and their corresponding results.

If a client retries a request because it did not receive an acknowledgement:

- The server checks whether the request ID has already been processed.
- If the request has already been processed, the server returns the original result.
- The operation must not be applied a second time.
- If the request has not been processed, the server validates and processes it normally.

Duplicate detection must be scoped to the originating client identity and retained for an agreed period.

This prevents accidental duplicate operations when clients retry requests.

## 13. Chat Protocol

Chat messages are sent to the server and distributed to the relevant room participants.

### 13.1 CHAT_MESSAGE

A client sends `CHAT_MESSAGE` to submit a message.

```json
{
    "protocol_version": 1,
    "type": "CHAT_MESSAGE",
    "message_id": "msg_030",
    "room_id": "room_101",
    "sender_id": "user_01",
    "timestamp": 1793990020,
    "payload": {
        "text": "Hello everyone!"
    }
}
```

### 13.2 CHAT_BROADCAST

After validating the message, the server broadcasts it to the room participants.

```json
{
    "protocol_version": 1,
    "type": "CHAT_BROADCAST",
    "message_id": "msg_031",
    "room_id": "room_101",
    "sender_id": "user_01",
    "timestamp": 1793990021,
    "payload": {
        "username": "Sahithi",
        "text": "Hello everyone!"
    }
}
```

The server determines the actual sender using the connection context.

Private messaging can be added through an extended chat payload if required.

## 14. Cursor Synchronization

Clients can periodically send cursor position updates so that other participants can see their activity on the shared board.

### CURSOR_UPDATE

```json
{
    "protocol_version": 1,
    "type": "CURSOR_UPDATE",
    "message_id": "msg_040",
    "room_id": "room_101",
    "sender_id": "user_01",
    "timestamp": 1793990030,
    "payload": {
        "x": 250,
        "y": 300
    }
}
```

The server relays cursor updates to the other participants in the same room.

Cursor updates are temporary and do not need to be stored as permanent board operations.

Clients should limit the frequency of cursor updates to avoid unnecessary network traffic.

## 15. Error Handling

The server must handle invalid messages and requests without terminating the entire application.

### ERROR

The server sends an `ERROR` message when a request cannot be processed.

```json
{
    "protocol_version": 1,
    "type": "ERROR",
    "message_id": "err_001",
    "room_id": "room_101",
    "sender_id": null,
    "timestamp": 1793990040,
    "payload": {
        "error_code": "INVALID_OPERATION",
        "message": "The requested operation is invalid.",
        "request_id": "msg_020"
    }
}
```

### Standard Error Codes

| Error Code | Description |
|---|---|
| `INVALID_MESSAGE` | Invalid message structure |
| `INVALID_JSON` | JSON parsing failed |
| `UNSUPPORTED_VERSION` | Unsupported protocol version |
| `UNKNOWN_MESSAGE_TYPE` | Unrecognized message type |
| `INVALID_USERNAME` | Invalid username |
| `ROOM_NOT_FOUND` | Requested room does not exist |
| `ROOM_ACCESS_DENIED` | User cannot access the room |
| `NOT_IN_ROOM` | User is not a room member |
| `PERMISSION_DENIED` | User lacks permission |
| `OBJECT_NOT_FOUND` | Requested object does not exist |
| `INVALID_OPERATION` | Operation payload is invalid |
| `MESSAGE_TOO_LARGE` | Message exceeds the size limit |
| `REQUEST_ID_CONFLICT` | Duplicate ID used with different request content |
| `INTERNAL_SERVER_ERROR` | Unexpected server-side failure |

The server should include the originating `request_id` whenever it can identify the request.

Malformed or oversized frames may require the server to close the connection if the message cannot be safely recovered.

## 16. Authentication and Connection Context

The server maintains a connection context for every connected client. This information is used to identify the client and verify its access to rooms and operations.

Example:

```python
connection_context = {
    "user_id": "user_01",
    "username": "Sahithi",
    "room_id": "room_101",
    "authenticated": True
}
```

The server is responsible for:

- Assigning and maintaining user identities.
- Associating each TCP connection with its registered user.
- Verifying room membership before processing room operations.
- Checking permissions before modifying shared state.
- Preventing users from impersonating others through client-provided `sender_id` values.

The `authenticated` field in this initial example represents a registered application session and does not indicate cryptographic authentication.

Any additional authentication mechanism can be specified separately if required.

## 17. Reconnection and State Recovery

If a client unexpectedly disconnects, it should be possible to restore its connection and synchronize it with the current room state.

### 17.1 RECONNECT

A client sends `RECONNECT` when attempting to restore a previous session.

```json
{
    "protocol_version": 1,
    "type": "RECONNECT",
    "message_id": "msg_050",
    "room_id": "room_101",
    "sender_id": "user_01",
    "timestamp": 1793990050,
    "payload": {
        "last_sequence_number": 25
    }
}
```

The server verifies the client's identity and room access before attempting recovery.

### 17.2 Recovery Behaviour

The server attempts to:

1. Identify the last sequence number received by the client.
2. Check whether the missing room events are available.
3. Send missing events in sequence order when possible.
4. Otherwise, send a complete `BOARD_SNAPSHOT` containing the latest board state and sequence number.

A snapshot must contain enough information to reconstruct the current shared board.

The exact recovery behaviour and event-retention rules will be finalized when the corresponding functionality is implemented.

## 18. Server-Side Message Processing

Every incoming client message passes through a validation and processing sequence.

1. Receive a complete framed message.
2. Decode the message using UTF-8.
3. Parse the JSON data.
4. Validate the common message envelope.
5. Check the protocol version.
6. Identify the connected user through the connection context.
7. Validate the message type.
8. Verify room membership where applicable.
9. Check user permissions.
10. Validate the message-specific payload.
11. Check for duplicate requests.
12. Apply the operation to the authoritative state.
13. Assign operation metadata and sequence numbers when applicable.
14. Send the acknowledgement.
15. Broadcast the accepted event to the relevant clients.

The exact order of acknowledgement and broadcasting must be consistent with the server's event-processing implementation. Both messages must refer to the same accepted operation.

Errors while processing one client's message must not cause the entire server to terminate.

## 19. Concurrency and Message Delivery

The server must support multiple clients communicating simultaneously.

The implementation must ensure:

- Independent handling of client connections.
- Thread-safe access to room and participant information.
- Safe concurrent access to shared objects.
- Consistent ordering of state-changing room operations.
- Prevention of message interleaving when multiple threads send data through the same socket.
- Disconnection of one client without affecting other active sessions.

All writes to a particular socket must be serialized. This can be achieved using a per-connection send lock or an outgoing message queue.

A consistent synchronization mechanism must also be used when processing operations within a room.

Clients must apply accepted room events according to their server-assigned sequence numbers.

## 20. Security and Validation Rules

The server must validate all incoming data before processing it. Client-provided information should not be assumed to be correct.

The following information must be checked:

- Message structure and protocol version.
- Message size.
- Message type.
- Sender identity.
- Room membership.
- User permissions.
- Object identifiers.
- Object coordinates and dimensions.
- Style properties.
- Chat message length.
- File metadata and file sizes.
- Values and data types in operation payloads.

Clients must not be allowed to impersonate other users, bypass room restrictions or directly overwrite the authoritative server state.

## 21. File and Image Transfer

Images and other large files must not be transmitted as ordinary JSON payloads.

A separate file-transfer mechanism will be used for image sharing and file attachments.

The mechanism should support:

- File metadata.
- File size validation.
- Transfer identification.
- Chunked transfer.
- Transfer completion verification.
- Handling of invalid or interrupted transfers.

The exact binary framing and transfer messages are not included in protocol version 1.0 and will be specified separately.

## 22. Future Extensions

The protocol can be extended to support additional collaboration and classroom features.

Possible extensions include:

- Private messaging.
- Live object selections and object-lock notifications.
- Undo and redo synchronization.
- Role-based permissions.
- Waiting rooms.
- Teacher and student modes.
- Individual student workspaces.
- Polls and announcements.
- Submission handling.
- Autosave and recovery.
- Version history.
- Activity logs.
- Binary file and image transfer.

New message types and their payload structures should be documented before implementation.

Existing message structures should not be changed incompatibly without updating the protocol version.

## 23. Protocol Agreement

This document describes the proposed communication structure for the WhiteBoard application.

All clients and the server should follow the same message envelope, framing mechanism and message definitions.

Changes to shared message structures, object representations or communication rules should be discussed and agreed upon by the team before implementation.

As development progresses, the protocol documentation will be updated to reflect any agreed changes and implementation details.

---

**Protocol Version:** 1.0  
**Status:** Proposed specification, pending team approval and implementation validation.