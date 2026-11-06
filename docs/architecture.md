# WhiteBoard – System Architecture

## 1. Project Overview

WhiteBoard is a LAN-based, multi-user collaborative whiteboard application developed using Python, PySide6 and TCP socket programming.

It allows multiple users connected to the same Local Area Network (LAN) to collaborate on a shared digital canvas without requiring an internet connection.

The application supports drawing, shapes, text, images, stickers, object editing, real-time collaboration, chat, user management and session persistence.

## 2. Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python 3.11+ |
| GUI framework | PySide6 |
| Communication | TCP sockets |
| Message format | JSON |
| Image processing | Pillow |
| Data persistence | SQLite / JSON |
| Version control | Git and GitHub |

The team may add dependencies when required and document them in `requirements.txt`.

## 3. Overall Architecture

The application follows a centralized client-server architecture.

- One computer runs the central server.
- Other computers connect to the server as clients.
- Each client provides the graphical interface and whiteboard tools.
- The server manages connected users, rooms and the authoritative shared whiteboard state.
- Client actions are sent to the server, validated and distributed to the other clients in the same room.

### 3.1 Architecture Components

#### Client Application

Each participant runs the client application.

Responsibilities:

- Display the whiteboard interface.
- Provide drawing, text, shape and image tools.
- Allow users to select, move, resize and rotate objects.
- Send user actions to the server.
- Receive updates from the server.
- Display updates from other participants.

#### Server Application

The server runs on one computer in the LAN.

Responsibilities:

- Accept incoming client connections.
- Manage connected users.
- Create and manage whiteboard rooms.
- Receive and validate client messages.
- Maintain the authoritative whiteboard state.
- Broadcast accepted updates to clients in the relevant room.
- Manage permissions and collaboration events.
- Support saving and restoring board data.

#### Shared Modules

The client and server use common modules to ensure that both sides follow the same data structures and communication format.

Responsibilities:

- Define the message protocol.
- Define shared whiteboard object models.
- Store common constants and message types.

## 4. Communication Flow

The application uses TCP sockets for reliable communication between clients and the server.

The general communication flow is:

1. A client connects to the server using its LAN IP address and port.
2. The client sends a request or an operation.
3. The server receives and decodes the message.
4. The server validates the request and checks permissions.
5. The server updates the appropriate room state when the operation is accepted.
6. The server broadcasts the accepted update to the other clients in that room.
7. Each client updates its local interface.

The server is authoritative for shared board state. Clients should not independently overwrite the shared state.

## 5. Initial Project Structure

```text
WhiteBoard/
│
├── client/
│   ├── main.py
│   ├── network/
│   ├── canvas/
│   ├── editor/
│   └── ui/
│
├── server/
│   ├── main.py
│   ├── network/
│   ├── rooms/
│   └── storage/
│
├── shared/
│   ├── protocol.py
│   ├── models.py
│   └── constants.py
│
├── assets/
│   ├── stickers/
│   └── icons/
│
├── docs/
│   ├── architecture.md
│   └── protocol.md
│
├── tests/
│
├── README.md
├── requirements.txt
├── .gitignore
└── LICENSE
```

## 6. Module Responsibilities and Ownership

| Member | Responsibility | Primary File Ownership |
|---|---|---|
| Member 1 | Server and network communication | `server/network/`, `server/rooms/` |
| Member 2 | Canvas rendering and drawing engine | `client/canvas/` |
| Member 3 | GUI, object editing and media tools | `client/ui/`, `client/editor/` |
| Member 4 | Collaboration, permissions and persistence | `server/storage/` and agreed collaboration modules |

The shared modules are common interfaces. Changes to these files must be discussed with the other members before implementation.

## 7. Shared Whiteboard Object Model

All whiteboard elements are represented as objects.

Each object contains common attributes:

- Unique object ID.
- Object type.
- Owner ID.
- Position.
- Width and height, where applicable.
- Rotation.
- Object-specific properties.

Example:

```json
{
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
```

Possible object types include:

- Freehand drawing
- Rectangle
- Circle
- Line
- Arrow
- Text
- Image
- Sticker
- Sticky note

Each type may have additional properties.

For example, text objects may contain font family, font size, bold, italic and alignment properties. Image objects may contain an asset reference.

## 8. Initial Client-Server Interfaces

The following function names are proposed interfaces. Their exact parameters and return values should be agreed upon by the responsible members before implementation.

### Client networking

- `connect(host, port)` – Connect to the server.
- `send_message(message)` – Send a message to the server.
- `disconnect()` – Close the connection.

### Server networking

- `start_server(host, port)` – Start listening for connections.
- `handle_client(connection)` – Handle a connected client.
- `broadcast(room_id, message)` – Send an update to clients in a room.

### Shared protocol

- `encode_message(message)` – Serialize and frame a message.
- `decode_message(data)` – Decode a received message.

### Shared models

- `create_object(data)` – Create a whiteboard object.
- `update_object(object_id, data)` – Update an object.
- `delete_object(object_id)` – Delete an object.

## 9. Important Design Decisions

1. TCP is used for client-server communication.
2. JSON is used for structured control messages.
3. TCP messages use length-prefix framing so that complete messages can be identified correctly.
4. The server maintains the authoritative shared board state.
5. Each whiteboard object has a unique ID.
6. Each room maintains its own shared board state.
7. The server validates operations before broadcasting them.
8. Large image and file transfers use a separate binary-transfer mechanism rather than embedding large files directly in JSON.
9. GUI operations and network communication must not block one another.
10. The application must work entirely over a LAN without requiring internet access.

## 10. Future Extensions

The architecture should allow the following features to be added in later development stages:

- Multiple rooms and session management.
- Live participant cursors.
- Group and private chat.
- User roles and permissions.
- Collaborative undo and redo.
- Autosave and recovery.
- Classroom mode.
- Export to PNG and PDF.
- Activity and version history.

These features will be implemented incrementally after the basic communication and drawing functionality is working.
