# WhiteBoard – Client-Server Communication Protocol

## 1. Overview

The WhiteBoard application uses TCP sockets for communication between clients and the central server.

JSON is used to represent structured messages exchanged between the client and server.

The protocol defines:

- Message structure.
- Message framing.
- Message types.
- Client-to-server communication.
- Server-to-client communication.
- Error responses.

Both client and server must follow this protocol.

## 2. Network Configuration

The server listens on a configurable IP address and port.

| Parameter | Description |
|---|---|
| Host | Server LAN IP address |
| Port | Configurable TCP port |
| Transport | TCP |
| Data format | JSON |
| Character encoding | UTF-8 |

During development, the server may bind to `0.0.0.0` to accept connections through available network interfaces.

Clients connect using the server computer's LAN IP address and configured port.

The actual port number will be finalized by the team.

## 3. Message Framing

TCP is a byte stream. It does not preserve individual message boundaries.

Therefore, the application must use message framing.

### Agreed framing format

Each message consists of:

1. A 4-byte unsigned integer representing the message length.
2. The message body containing UTF-8 encoded JSON.

The length is stored in network byte order (big-endian).

```text
+----------------------+---------------------------+
| 4-byte message length| JSON message body         |
+----------------------+---------------------------+
```

Example:

```text
[Length Header][UTF-8 JSON Data]
```

The receiver must:

1. Read exactly 4 bytes for the header.
2. Decode the header to obtain the message length.
3. Read exactly that many bytes.
4. Decode the received bytes as UTF-8.
5. Parse the JSON message.

The receiver must handle partial reads because a single `recv()` call may not return all requested bytes.

A maximum message size must be configured to prevent excessively large messages.

Large image and file transfers will use a separately defined binary-transfer protocol.

## 4. Standard Message Envelope

All structured application messages follow this common format:

```json
{
  "type": "MESSAGE_TYPE",
  "message_id": "msg_001",
  "room_id": "room_101",
  "sender_id": "user_01",
  "payload": {}
}
```

### Field descriptions

| Field | Data type | Description |
|---|---|---|
| `type` | String | Identifies the message operation |
| `message_id` | String | Unique identifier for the message |
| `room_id` | String or null | Identifies the target room |
| `sender_id` | String or null | Identifies the sender |
| `payload` | Object | Contains operation-specific data |

The server may add server-generated metadata, such as a sequence number, to accepted events.

For server-generated messages, `sender_id` may be null or a designated server identifier, depending on the message type.

## 5. Initial Message Types

The following message types are proposed for the application.

### 5.1 Connection and user management

| Message type | Direction | Purpose |
|---|---|---|
| `CONNECT` | Client → Server | Request a connection or identify the user |
| `CONNECT_SUCCESS` | Server → Client | Confirm successful connection |
| `CONNECT_ERROR` | Server → Client | Report connection failure |
| `DISCONNECT` | Client → Server | Request disconnection |
| `USER_JOINED` | Server → Clients | Notify room participants |
| `USER_LEFT` | Server → Clients | Notify room participants |

### 5.2 Room management

| Message type | Direction | Purpose |
|---|---|---|
| `CREATE_ROOM` | Client → Server | Request room creation |
| `JOIN_ROOM` | Client → Server | Request to join a room |
| `LEAVE_ROOM` | Client → Server | Leave a room |
| `ROOM_CREATED` | Server → Client | Confirm room creation |
| `ROOM_JOINED` | Server → Client | Confirm room membership |
| `ROOM_ERROR` | Server → Client | Report a room-related error |

### 5.3 Whiteboard operations

| Message type | Direction | Purpose |
|---|---|---|
| `CREATE_OBJECT` | Client → Server | Request creation of a canvas object |
| `UPDATE_OBJECT` | Client → Server | Request modification of an object |
| `DELETE_OBJECT` | Client → Server | Request deletion of an object |
| `OBJECT_CREATED` | Server → Clients | Broadcast an accepted object creation |
| `OBJECT_UPDATED` | Server → Clients | Broadcast an accepted object update |
| `OBJECT_DELETED` | Server → Clients | Broadcast an accepted object deletion |
| `BOARD_SNAPSHOT` | Server → Client | Send the current board state |

These operations apply to supported object types, including drawings, shapes, text, images and stickers.

### 5.4 Collaboration

| Message type | Direction | Purpose |
|---|---|---|
| `CURSOR_UPDATE` | Client → Server | Send cursor position |
| `CHAT_MESSAGE` | Client → Server | Send a chat message |
| `CHAT_BROADCAST` | Server → Clients | Deliver a chat message |
| `UNDO_REQUEST` | Client → Server | Request undo |
| `REDO_REQUEST` | Client → Server | Request redo |
| `ERROR` | Server → Client | Report a failed or rejected operation |

Additional message types can be introduced as new features are implemented.

## 6. Example Messages

### 6.1 Client connection request

```json
{
  "type": "CONNECT",
  "message_id": "msg_001",
  "room_id": null,
  "sender_id": "user_01",
  "payload": {
    "username": "Sahithi"
  }
}
```

### 6.2 Create room request

```json
{
  "type": "CREATE_ROOM",
  "message_id": "msg_002",
  "room_id": null,
  "sender_id": "user_01",
  "payload": {
    "room_name": "Team Whiteboard"
  }
}
```

### 6.3 Join room request

```json
{
  "type": "JOIN_ROOM",
  "message_id": "msg_003",
  "room_id": "room_101",
  "sender_id": "user_02",
  "payload": {}
}
```

### 6.4 Create rectangle request

```json
{
  "type": "CREATE_OBJECT",
  "message_id": "msg_004",
  "room_id": "room_101",
  "sender_id": "user_01",
  "payload": {
    "object": {
      "id": "obj_001",
      "type": "rectangle",
      "owner_id": "user_01",
      "x": 100,
      "y": 150,
      "width": 200,
      "height": 100,
      "rotation": 0,
      "properties": {
        "color": "#000000",
        "fill_color": "#FFFFFF",
        "line_width": 3
      }
    }
  }
}
```

The client requests the operation. The server validates it, assigns authoritative metadata such as a sequence number, updates the board state and broadcasts an `OBJECT_CREATED` event.

### 6.5 Update object request

```json
{
  "type": "UPDATE_OBJECT",
  "message_id": "msg_005",
  "room_id": "room_101",
  "sender_id": "user_01",
  "payload": {
    "object_id": "obj_001",
    "changes": {
      "x": 250,
      "y": 200,
      "rotation": 30
    }
  }
}
```

### 6.6 Delete object request

```json
{
  "type": "DELETE_OBJECT",
  "message_id": "msg_006",
  "room_id": "room_101",
  "sender_id": "user_01",
  "payload": {
    "object_id": "obj_001"
  }
}
```

### 6.7 Chat message

```json
{
  "type": "CHAT_MESSAGE",
  "message_id": "msg_007",
  "room_id": "room_101",
  "sender_id": "user_01",
  "payload": {
    "text": "Hello everyone!"
  }
}
```

### 6.8 Error response

```json
{
  "type": "ERROR",
  "message_id": "msg_008",
  "room_id": "room_101",
  "sender_id": null,
  "payload": {
    "error_code": "PERMISSION_DENIED",
    "message": "You are not allowed to modify this object."
  }
}
```

## 7. Server Processing Rules

For every client operation, the server must:

1. Receive and decode the complete message.
2. Validate the message structure and required fields.
3. Identify the connected user.
4. Verify room membership.
5. Check the user's permissions for the requested operation.
6. Validate the target object and operation data.
7. Apply the operation to the authoritative room state.
8. Assign server-side event metadata where applicable.
9. Broadcast the accepted event to clients in that room.

Rejected operations must not modify the shared board state.

The server must not trust the `sender_id` supplied by a client as proof of identity. It must associate incoming messages with the authenticated or registered connection.

## 8. Message Ordering and Duplicate Handling

The server should assign an increasing sequence number to accepted room events.

This allows clients to identify the order in which the server accepted operations.

The `message_id` field can be used to identify repeated requests and support duplicate handling.

The exact acknowledgement and retry mechanism will be finalized during networking implementation.

## 9. Error Handling

The application should handle:

- Invalid JSON.
- Incomplete messages.
- Messages exceeding the configured size limit.
- Unknown message types.
- Invalid room IDs.
- Unauthorized operations.
- Disconnected clients.
- Connection timeouts.
- Unexpected server errors.

Errors should be reported without crashing the entire server or client application.

## 10. Future Protocol Extensions

The protocol may be extended to support:

- Binary image and file transfers.
- Live cursors and selection indicators.
- Role and permission updates.
- Collaborative undo and redo.
- Autosave and board recovery.
- Classroom mode.
- Version history and activity events.

New message types and changes to the common envelope must be documented and communicated to all team members before implementation.
