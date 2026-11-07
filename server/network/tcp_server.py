import socket
import threading
import uuid

from dataclasses import dataclass, field

from shared.protocol import (
    create_message,
    send_message,
    receive_message
)

from shared.constants import (
    PROTOCOL_VERSION,
    DEFAULT_HOST,
    DEFAULT_PORT,

    CONNECT,
    CONNECT_SUCCESS,
    CONNECT_ERROR,
    DISCONNECT,

    PING,
    PONG,

    USER_JOINED,
    USER_LEFT,

    CHAT_MESSAGE,
    CHAT_BROADCAST,

    ERROR,

    CREATE_ROOM,
    ROOM_CREATED,

    JOIN_ROOM,
    ROOM_JOINED,

    LEAVE_ROOM,
    ROOM_LEFT,

    ROOM_ERROR,

    GET_ROOM_PARTICIPANTS,
    ROOM_PARTICIPANTS
)

from server.rooms.room_manager import RoomManager


@dataclass
class ClientConnection:

    sock: socket.socket
    user_id: str
    username: str

    send_lock: threading.Lock = field(
        default_factory=threading.Lock
    )


class WhiteboardServer:

    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):

        self.host = host
        self.port = port
        self.bound_port = None

        self.server_socket = None

        self.running = threading.Event()
        self.ready = threading.Event()

        self.clients = {}
        self.clients_lock = threading.Lock()

        self.room_manager = RoomManager()

    def serve_forever(self):

        self.server_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        self.server_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )

        try:

            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen()
            self.server_socket.settimeout(1.0)

            self.bound_port = self.server_socket.getsockname()[1]

            self.running.set()
            self.ready.set()

            print(
                f"Server listening on "
                f"{self.host}:{self.bound_port}"
            )

            while self.running.is_set():

                try:
                    client_socket, address = self.server_socket.accept()

                except socket.timeout:
                    continue

                except OSError:
                    if self.running.is_set():
                        raise
                    break

                print(f"Incoming connection from {address}")

                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address),
                    daemon=True
                )

                client_thread.start()

        finally:

            self.running.clear()

            if self.server_socket:
                self.server_socket.close()

            print("Server stopped.")

    def handle_client(self, client_socket, address):

        client = None

        try:

            first_message = receive_message(client_socket)

            if first_message is None:
                return

            if first_message.get("protocol_version") != PROTOCOL_VERSION:

                self.send_connect_error(
                    client_socket,
                    "Unsupported protocol version."
                )
                return

            if first_message.get("type") != CONNECT:

                self.send_connect_error(
                    client_socket,
                    "Expected CONNECT as the first message."
                )
                return

            payload = first_message.get("payload", {})

            if not isinstance(payload, dict):
                self.send_connect_error(
                    client_socket,
                    "Invalid connection payload."
                )
                return

            username = payload.get("username", "")

            if not isinstance(username, str):

                self.send_connect_error(
                    client_socket,
                    "Username must be a string."
                )
                return

            username = username.strip()

            if not username or len(username) > 30:

                self.send_connect_error(
                    client_socket,
                    "Username must contain between 1 and 30 characters."
                )
                return

<<<<<<< Updated upstream
            
            # Check whether the username is already in use.
            # Keep the check and registration inside the same lock
            # to prevent simultaneous duplicate connections.
            with self.clients_lock:

                username_taken = any(
                    existing_client.username.casefold() == username.casefold()
                    for existing_client in self.clients.values()
                )

                if username_taken:
=======
            user_id = uuid.uuid4().hex[:12]

            client = ClientConnection(
                sock=client_socket,
                user_id=user_id,
                username=username
            )

            # Duplicate username check and registration must be atomic.
            with self.clients_lock:

                duplicate = any(
                    existing.username.casefold() == username.casefold()
                    for existing in self.clients.values()
                )

                if duplicate:

>>>>>>> Stashed changes
                    self.send_connect_error(
                        client_socket,
                        "Username already taken."
                    )
<<<<<<< Updated upstream
                    return

                # The server assigns the identity.
                user_id = uuid.uuid4().hex[:12]

                client = ClientConnection(
                    sock=client_socket,
                    user_id=user_id,
                    username=username
                )

                # Register the client before confirming the connection.
                self.clients[user_id] = client

                response = create_message(
                    CONNECT_SUCCESS,
                    payload={
                        "user_id": user_id,
                        "username": username,
                        "message": "Connected successfully."
                    },
                    sender_id="SERVER"
                )

                send_message(
                    client_socket,
                    response,
                    client.send_lock
=======

                    return

                self.clients[user_id] = client

                self.send_to_client(
                    client,
                    create_message(
                        CONNECT_SUCCESS,
                        payload={
                            "user_id": user_id,
                            "username": username,
                            "message": "Connected successfully."
                        },
                        sender_id="SERVER"
                    )
>>>>>>> Stashed changes
                )

            print(f"{username} connected with ID {user_id}")

            self.broadcast_global(
                create_message(
                    USER_JOINED,
                    payload={
                        "user_id": user_id,
                        "username": username
                    },
                    sender_id="SERVER"
                ),
                exclude_user_id=user_id
            )

            while self.running.is_set():

                message = receive_message(client_socket)

                if message is None:
                    break

                if not isinstance(message.get("payload", {}), dict):
                    self.send_error(client, "Invalid message payload.")
                    continue

                message_type = message.get("type")
                payload = message.get("payload", {})

                if message_type == PING:

                    self.send_to_client(
                        client,
                        create_message(
                            PONG,
                            payload={"message": "Server is alive."},
                            sender_id="SERVER"
                        )
                    )

                elif message_type == CHAT_MESSAGE:

                    self.handle_chat(client, payload)

                elif message_type == CREATE_ROOM:

                    self.handle_create_room(client, payload)

                elif message_type == JOIN_ROOM:

                    self.handle_join_room(client, payload)

                elif message_type == LEAVE_ROOM:

                    self.handle_leave_room(client)

                elif message_type == GET_ROOM_PARTICIPANTS:

                    self.handle_get_participants(client)

                elif message_type == DISCONNECT:

                    break

                else:

                    self.send_error(
                        client,
                        f"Unsupported message type: {message_type}"
                    )

        except (ConnectionError, OSError, ValueError) as error:

            print(f"Connection error from {address}: {error}")

        finally:

            if client is not None:

                # Remove the client from their room before disconnecting.
                self.remove_client_from_room(client)

                with self.clients_lock:
                    self.clients.pop(client.user_id, None)

                print(f"{client.username} disconnected.")

                self.broadcast_global(
                    create_message(
                        USER_LEFT,
                        payload={
                            "user_id": client.user_id,
                            "username": client.username
                        },
                        sender_id="SERVER"
                    ),
                    exclude_user_id=client.user_id
                )

            try:
                client_socket.close()
            except OSError:
                pass

    # ---------------------------------------------------------
    # CHAT
    # ---------------------------------------------------------

    def handle_chat(self, client, payload):

        chat_text = payload.get("text", "")

        if not isinstance(chat_text, str):

            self.send_error(client, "Chat text must be a string.")
            return

        chat_text = chat_text.strip()

        if not chat_text or len(chat_text) > 2000:

            self.send_error(
                client,
                "Chat text must contain 1 to 2000 characters."
            )
            return

        room_id = self.room_manager.get_user_room_id(client.user_id)

        if room_id is None:

            self.send_error(
                client,
                "Create or join a room before sending chat messages."
            )
            return

        event = create_message(
            CHAT_BROADCAST,
            room_id=room_id,
            payload={
                "text": chat_text,
                "username": client.username
            },
            sender_id=client.user_id
        )

        self.broadcast_to_room(room_id, event)

    # ---------------------------------------------------------
    # CREATE ROOM
    # ---------------------------------------------------------

    def handle_create_room(self, client, payload):

        room_name = payload.get("name", "Untitled Room")

        try:

            room = self.room_manager.create_room(
                client.user_id,
                client.username,
                room_name
            )

            self.send_to_client(
                client,
                create_message(
                    ROOM_CREATED,
                    room_id=room["room_id"],
                    payload=room,
                    sender_id="SERVER"
                )
            )

            print(
                f"{client.username} created room "
                f"{room['room_id']}"
            )

        except ValueError as error:

            self.send_room_error(client, str(error))

    # ---------------------------------------------------------
    # JOIN ROOM
    # ---------------------------------------------------------

    def handle_join_room(self, client, payload):

        room_id = payload.get("room_id", "")

        try:

            room = self.room_manager.join_room(
                client.user_id,
                client.username,
                room_id
            )

            room_id = room["room_id"]

            self.send_to_client(
                client,
                create_message(
                    ROOM_JOINED,
                    room_id=room_id,
                    payload=room,
                    sender_id="SERVER"
                )
            )

            self.broadcast_to_room(
                room_id,
                create_message(
                    USER_JOINED,
                    room_id=room_id,
                    payload={
                        "user_id": client.user_id,
                        "username": client.username
                    },
                    sender_id="SERVER"
                ),
                exclude_user_id=client.user_id
            )

            self.broadcast_room_participants(room_id)

            print(
                f"{client.username} joined room {room_id}"
            )

        except ValueError as error:

            self.send_room_error(client, str(error))

    # ---------------------------------------------------------
    # LEAVE ROOM
    # ---------------------------------------------------------

    def handle_leave_room(self, client):

        try:

            result = self.room_manager.leave_room(client.user_id)

            room_id = result["room_id"]

            self.send_to_client(
                client,
                create_message(
                    ROOM_LEFT,
                    room_id=room_id,
                    payload=result,
                    sender_id="SERVER"
                )
            )

            if not result["room_deleted"]:

                self.broadcast_to_room(
                    room_id,
                    create_message(
                        USER_LEFT,
                        room_id=room_id,
                        payload={
                            "user_id": client.user_id,
                            "username": client.username,
                            "new_host_id": result["new_host_id"]
                        },
                        sender_id="SERVER"
                    )
                )

                self.broadcast_room_participants(room_id)

            print(
                f"{client.username} left room {room_id}"
            )

        except ValueError as error:

            self.send_room_error(client, str(error))

    # ---------------------------------------------------------
    # PARTICIPANT LIST
    # ---------------------------------------------------------

    def handle_get_participants(self, client):

        room_id = self.room_manager.get_user_room_id(client.user_id)

        if room_id is None:

            self.send_room_error(
                client,
                "You are not in a room."
            )
            return

        self.send_participants_to_client(client, room_id)

    def send_participants_to_client(self, client, room_id):

        try:

            participants = self.room_manager.get_participants(room_id)

            room = self.room_manager.get_room_snapshot(room_id)

            self.send_to_client(
                client,
                create_message(
                    ROOM_PARTICIPANTS,
                    room_id=room_id,
                    payload={
                        "room_id": room_id,
                        "room_name": room["name"],
                        "host_id": room["host_id"],
                        "participants": participants
                    },
                    sender_id="SERVER"
                )
            )

        except ValueError as error:

            self.send_room_error(client, str(error))

    def broadcast_room_participants(self, room_id):

        try:

            participants = self.room_manager.get_participants(room_id)

            room = self.room_manager.get_room_snapshot(room_id)

            event = create_message(
                ROOM_PARTICIPANTS,
                room_id=room_id,
                payload={
                    "room_id": room_id,
                    "room_name": room["name"],
                    "host_id": room["host_id"],
                    "participants": participants
                },
                sender_id="SERVER"
            )

            self.broadcast_to_room(room_id, event)

        except ValueError:
            pass

    # ---------------------------------------------------------
    # DISCONNECTION CLEANUP
    # ---------------------------------------------------------

    def remove_client_from_room(self, client):

        room_id = self.room_manager.get_user_room_id(client.user_id)

        if room_id is None:
            return

        try:

            result = self.room_manager.leave_room(client.user_id)

            if not result["room_deleted"]:

                self.broadcast_to_room(
                    room_id,
                    create_message(
                        USER_LEFT,
                        room_id=room_id,
                        payload={
                            "user_id": client.user_id,
                            "username": client.username,
                            "new_host_id": result["new_host_id"]
                        },
                        sender_id="SERVER"
                    )
                )

                self.broadcast_room_participants(room_id)

        except ValueError:
            pass

    # ---------------------------------------------------------
    # BROADCASTING
    # ---------------------------------------------------------

    def broadcast_to_room(
        self,
        room_id,
        message,
        exclude_user_id=None
    ):

        try:
            participants = self.room_manager.get_participants(room_id)
        except ValueError:
            return

        user_ids = [
            participant["user_id"]
            for participant in participants
            if participant["user_id"] != exclude_user_id
        ]

        with self.clients_lock:
            clients_snapshot = [
                self.clients[user_id]
                for user_id in user_ids
                if user_id in self.clients
            ]

        for client in clients_snapshot:
            self.send_to_client(client, message)

    def broadcast_global(self, message, exclude_user_id=None):

        with self.clients_lock:
            clients_snapshot = [
                client
                for user_id, client in self.clients.items()
                if user_id != exclude_user_id
            ]

        for client in clients_snapshot:
            self.send_to_client(client, message)

    # ---------------------------------------------------------
    # SENDING MESSAGES
    # ---------------------------------------------------------

    def send_to_client(self, client, message):

        try:

            send_message(
                client.sock,
                message,
                client.send_lock
            )

        except (OSError, ValueError):

            try:
                client.sock.close()
            except OSError:
                pass

    def send_connect_error(self, client_socket, error_text):

        message = create_message(
            CONNECT_ERROR,
            payload={"message": error_text},
            sender_id="SERVER"
        )

        try:
            send_message(client_socket, message)
        except (OSError, ValueError):
            pass

    def send_error(self, client, error_text):

        self.send_to_client(
            client,
            create_message(
                ERROR,
                payload={"message": error_text},
                sender_id="SERVER"
            )
        )

    def send_room_error(self, client, error_text):

        self.send_to_client(
            client,
            create_message(
                ROOM_ERROR,
                payload={"message": error_text},
                sender_id="SERVER"
            )
        )

    # ---------------------------------------------------------
    # SHUTDOWN
    # ---------------------------------------------------------

    def shutdown(self):

        self.running.clear()

        if self.server_socket:

            try:
                self.server_socket.close()
            except OSError:
                pass

        with self.clients_lock:
            clients_snapshot = list(self.clients.values())

        for client in clients_snapshot:

            try:
                client.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

            try:
                client.sock.close()
            except OSError:
                pass