import socket
import threading
import uuid

from dataclasses import dataclass, field

from shared.protocol import create_message, send_message, receive_message

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
    ERROR
)


@dataclass
class ClientConnection:
    """
    Stores information about one connected client.
    """

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

    def serve_forever(self):
        """
        Starts the server and continuously accepts clients.
        """

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
        """
        Handles communication with one client.
        """

        client = None

        try:
            # The first message must be CONNECT.
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

            username = payload.get("username", "")

            if not isinstance(username, str):
                self.send_error(
                    client_socket,
                    "Username must be a string."
                )
                return

            username = username.strip()

            if not username or len(username) > 30:
                self.send_error(
                    client_socket,
                    "Username must contain between 1 and 30 characters."
                )
                return

            
            # Check whether the username is already in use.
            # Keep the check and registration inside the same lock
            # to prevent simultaneous duplicate connections.
            with self.clients_lock:

                username_taken = any(
                    existing_client.username.casefold() == username.casefold()
                    for existing_client in self.clients.values()
                )

                if username_taken:
                    self.send_connect_error(
                        client_socket,
                        "Username already taken."
                    )
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
                )

            print(f"{username} connected with ID {user_id}")

            self.broadcast(
                create_message(
                    USER_JOINED,
                    payload={
                        "user_id": user_id,
                        "username": username
                    },
                    sender_id="SERVER"
                )
            )

            # Handle subsequent messages.
            while self.running.is_set():

                message = receive_message(client_socket)

                if message is None:
                    break

                message_type = message.get("type")

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

                    chat_text = message.get(
                        "payload", {}
                    ).get("text", "")

                    if not isinstance(chat_text, str):
                        self.send_error(
                            client_socket,
                            "Chat text must be a string."
                        )
                        continue

                    chat_text = chat_text.strip()

                    if not chat_text or len(chat_text) > 2000:
                        self.send_error(
                            client_socket,
                            "Chat text must contain 1 to 2000 characters."
                        )
                        continue

                    # Do not trust sender_id supplied by the client.
                    event = create_message(
                        CHAT_BROADCAST,
                        payload={
                            "text": chat_text,
                            "username": client.username
                        },
                        sender_id=client.user_id
                    )

                    self.broadcast(event)

                elif message_type == DISCONNECT:
                    break

                else:
                    self.send_error(
                        client_socket,
                        f"Unsupported message type: {message_type}"
                    )

        except (ConnectionError, OSError, ValueError) as error:
            print(f"Connection error from {address}: {error}")

        finally:

            if client is not None:

                with self.clients_lock:
                    self.clients.pop(client.user_id, None)

                print(f"{client.username} disconnected.")

                self.broadcast(
                    create_message(
                        USER_LEFT,
                        payload={
                            "user_id": client.user_id,
                            "username": client.username
                        },
                        sender_id="SERVER"
                    )
                )

            try:
                client_socket.close()
            except OSError:
                pass

    def send_to_client(self, client, message):
        """
        Sends a message to one client.
        """

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

    def broadcast(self, message):
        """
        Sends a message to all currently registered clients.
        """

        with self.clients_lock:
            clients_snapshot = list(self.clients.values())

        for client in clients_snapshot:
            self.send_to_client(client, message)

    def send_connect_error(self, client_socket, error_text):
        """
        Sends a CONNECT_ERROR message during the handshake.
        """

        message = create_message(
            CONNECT_ERROR,
            payload={"message": error_text},
            sender_id="SERVER"
        )

        try:
            send_message(client_socket, message)
        except (OSError, ValueError):
            pass

    def send_error(self, client_socket, error_text):
        """
        Sends an ERROR message to a client.
        """

        message = create_message(
            ERROR,
            payload={"message": error_text},
            sender_id="SERVER"
        )

        try:
            send_message(client_socket, message)
        except (OSError, ValueError):
            pass

    def shutdown(self):
        """
        Stops the server and closes active connections.
        """

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